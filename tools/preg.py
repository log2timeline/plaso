#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Parse your Windows Registry files using preg.

preg is a simple Windows Registry parser using the plaso Registry plugins and
image parsing capabilities. It uses the back-end libraries of plaso to read
raw image files and extract Registry files from VSS and restore points and then
runs the Registry plugins of plaso against the Registry hive and presents it
in a textual format.
"""

from __future__ import print_function
import argparse
import locale
import logging
import os
import re
import sys
import textwrap

try:
  # Support version 1.X of IPython.
  # pylint: disable=no-name-in-module
  from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
  # pylint: disable=no-name-in-module
  from IPython.frontend.terminal.embed import InteractiveShellEmbed

import IPython
from IPython.config.loader import Config
from IPython.core import magic

import pysmdev

from dfvfs.helpers import source_scanner
from dfvfs.helpers import windows_path_resolver
from dfvfs.lib import definitions
from dfvfs.resolver import resolver
from dfvfs.volume import tsk_volume_system

from plaso.cli import hexdump
from plaso.cli import storage_media_tool
from plaso.cli import tools as cli_tools
from plaso.cli import views as cli_views
from plaso.engine import knowledge_base
from plaso.frontend import preg
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import


# Older versions of IPython don't have a version_info attribute.
if getattr(IPython, u'version_info', (0, 0, 0)) < (1, 2, 1):
  raise ImportWarning(
      u'Preg requires at least IPython version 1.2.1.')


class PregTool(storage_media_tool.StorageMediaTool):
  """Class that implements the preg CLI tool.

  Attributes:
    plugin_names: a list containing names of selected Windows Registry plugins
                  to be used, defaults to an empty list.
    registry_file: a string containing the path to a Windows Registry file or
                   a Registry file type, eg: NTUSER, SOFTWARE, etc.
    run_mode: the run mode of the tool, determines if the tool should
              be running in a plugin mode, parsing an entire Registry file,
              being run in a console, etc.
    source_type: dfVFS source type indicator for the source file.
  """

  # Assign a default value to font align length.
  _DEFAULT_FORMAT_ALIGN_LENGTH = 15

  _SOURCE_OPTION = u'image'

  _WINDOWS_DIRECTORIES = frozenset([
      u'C:\\Windows',
      u'C:\\WINNT',
      u'C:\\WTSRV',
      u'C:\\WINNT35',
  ])

  NAME = u'preg'

  DESCRIPTION = textwrap.dedent(u'\n'.join([
      u'preg is a Windows Registry parser using the plaso Registry plugins ',
      u'and storage media image parsing capabilities.',
      u'',
      u'It uses the back-end libraries of plaso to read raw image files and',
      u'extract Registry files from VSS and restore points and then runs the',
      u'Registry plugins of plaso against the Registry hive and presents it',
      u'in a textual format.']))

  EPILOG = textwrap.dedent(u'\n'.join([
      u'',
      u'Example usage:',
      u'',
      u'Parse the SOFTWARE hive from an image:',
      (u'  preg.py [--vss] [--vss-stores VSS_STORES] -i IMAGE_PATH '
       u'[-o OFFSET] -c SOFTWARE'),
      u'',
      u'Parse an userassist key within an extracted hive:',
      u'  preg.py -p userassist MYNTUSER.DAT',
      u'',
      u'Parse the run key from all Registry keys (in vss too):',
      u'  preg.py --vss -i IMAGE_PATH [-o OFFSET] -p run',
      u'',
      u'Open up a console session for the SYSTEM hive inside an image:',
      u'  preg.py -i IMAGE_PATH [-o OFFSET] -c SYSTEM',
      u'']))

  # Define the different run modes.
  RUN_MODE_CONSOLE = 1
  RUN_MODE_LIST_PLUGINS = 2
  RUN_MODE_REG_FILE = 3
  RUN_MODE_REG_PLUGIN = 4
  RUN_MODE_REG_KEY = 5

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: optional input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: optional output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(PregTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._front_end = preg.PregFrontend()
    self._key_path = None
    self._knowledge_base_object = knowledge_base.KnowledgeBase()
    self._parse_restore_points = False
    self._path_resolvers = []
    self._verbose_output = False
    self._windows_directory = u''

    self.plugin_names = []
    self.registry_file = u''
    self.run_mode = None
    self.source_type = None

  def _GetEventDataHexDump(
      self, event_object, before=0, maximum_number_of_lines=20):
    """Returns a hexadecimal representation of the event data.

     This function creates a hexadecimal string representation based on
     the event data described by the event object.

    Args:
      event_object: The event object (instance of EventObject).
      before: Optional number of bytes to include in the output before
              the event. The default is none.
      maximum_number_of_lines: Optional maximum number of lines to include
                               in the output. The default is 20.

    Returns:
      A string that contains the hexadecimal representation of the event data.
    """
    if not event_object:
      return u'Missing event object.'

    if not hasattr(event_object, u'pathspec'):
      return u'Event object has no path specification.'

    try:
      file_entry = resolver.Resolver.OpenFileEntry(event_object.pathspec)
    except IOError as exception:
      return u'Unable to open file with error: {0:s}'.format(exception)

    offset = getattr(event_object, u'offset', 0)
    if offset - before > 0:
      offset -= before

    file_object = file_entry.GetFileObject()
    file_object.seek(offset, os.SEEK_SET)
    data_size = maximum_number_of_lines * 16
    data = file_object.read(data_size)
    file_object.close()

    return hexdump.Hexdump.FormatData(data)

  def _GetFormatString(self, event_object):
    """Return back a format string that can be used for a given event object."""
    # Go through the attributes and see if there is an attribute
    # value that is longer than the default font align length, and adjust
    # it accordingly if found.
    if hasattr(event_object, u'regvalue'):
      attributes = event_object.regvalue.keys()
    else:
      all_attributes = event_object.GetAttributes()
      attributes = all_attributes.difference(
          event_object.COMPARE_EXCLUDE)

    align_length = self._DEFAULT_FORMAT_ALIGN_LENGTH
    for attribute in attributes:
      attribute_len = len(attribute)
      if attribute_len > align_length and attribute_len < 30:
        align_length = len(attribute)

    # Create the format string that will be used, using variable length
    # font align length (calculated in the prior step).
    return u'{{0:>{0:d}s}} : {{1!s}}'.format(align_length)

  def _GetTSKPartitionIdentifiers(
      self, scan_node, partition_string=None, partition_offset=None):
    """Determines the TSK partition identifiers.

    This method first checks for the preferred partition number, then for
    the preferred partition offset and falls back to prompt the user if
    no usable preferences were specified.

    Args:
      scan_node: the scan node (instance of dfvfs.ScanNode).
      partition_string: optional preferred partition number string. The default
                        is None.
      partition_offset: optional preferred partition byte offset. The default
                        is None.

    Returns:
      A list of partition identifiers.

    Raises:
      RuntimeError: if the volume for a specific identifier cannot be
                    retrieved.
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan node is invalid.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError(u'Invalid scan node.')

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    # TODO: refactor to front-end.
    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      logging.info(u'No partitions found.')
      return

    # Go over all the detected volume identifiers and only include
    # detected Windows partitions.
    windows_volume_identifiers = self.GetWindowsVolumeIdentifiers(
        scan_node, volume_identifiers)

    if not windows_volume_identifiers:
      logging.error(u'No Windows partitions discovered.')
      return windows_volume_identifiers

    if partition_string == u'all':
      return windows_volume_identifiers

    if partition_string is not None and not partition_string.startswith(u'p'):
      return windows_volume_identifiers

    partition_number = None
    if partition_string:
      try:
        partition_number = int(partition_string[1:], 10)
      except ValueError:
        pass

    if partition_number is not None and partition_number > 0:
      # Plaso uses partition numbers starting with 1 while dfvfs expects
      # the volume index to start with 0.
      volume = volume_system.GetVolumeByIndex(partition_number - 1)
      partition_string = u'p{0:d}'.format(partition_number)
      if volume and partition_string in windows_volume_identifiers:
        return [partition_string]

      logging.warning(u'No such partition: {0:d}.'.format(partition_number))

    if partition_offset is not None:
      for volume in volume_system.volumes:
        volume_extent = volume.extents[0]
        if volume_extent.offset == partition_offset:
          return [volume.identifier]

      logging.warning(
          u'No such partition with offset: {0:d} (0x{0:08x}).'.format(
              partition_offset))

    if len(windows_volume_identifiers) == 1:
      return windows_volume_identifiers

    try:
      selected_volume_identifier = self._PromptUserForPartitionIdentifier(
          volume_system, windows_volume_identifiers)
    except KeyboardInterrupt:
      raise errors.UserAbort(u'File system scan aborted.')

    if selected_volume_identifier == u'all':
      return windows_volume_identifiers

    return [selected_volume_identifier]

  # TODO: Improve check and use dfVFS.
  def _PathExists(self, file_path):
    """Determine if a given file path exists as a file, directory or a device.

    Args:
      file_path: string denoting the file path that needs checking.

    Returns:
      A tuple, a boolean indicating whether or not the path exists and
      a string that contains the reason, if any, why this was not
      determined to be a file.
    """
    if os.path.exists(file_path):
      return True, u''

    try:
      if pysmdev.check_device(file_path):
        return True, u''
    except IOError as exception:
      return False, u'Unable to determine, with error: {0:s}'.format(exception)

    return False, u'Not an existing file.'

  def _PrintEventBody(self, event_object, file_entry=None, show_hex=False):
    """Writes a list of strings extracted from an event to an output writer.

    Args:
      event_object: event object (instance of event.EventObject).
      file_entry: optional file entry object (instance of dfvfs.FileEntry)
                  that the event originated from. Default is None.
      show_hex: optional boolean to indicate that the hexadecimal representation
                of the event should be included in the output. The default is
                False.
    """
    format_string = self._GetFormatString(event_object)

    timestamp_description = getattr(
        event_object, u'timestamp_desc', eventdata.EventTimestamp.WRITTEN_TIME)

    if timestamp_description != eventdata.EventTimestamp.WRITTEN_TIME:
      self._output_writer.Write(u'<{0:s}>\n'.format(timestamp_description))

    if hasattr(event_object, u'regvalue'):
      attributes = event_object.regvalue
    else:
      # TODO: Add a function for this to avoid repeating code.
      keys = event_object.GetAttributes().difference(
          event_object.COMPARE_EXCLUDE)
      keys.discard(u'offset')
      keys.discard(u'timestamp_desc')
      attributes = {}
      for key in keys:
        attributes[key] = getattr(event_object, key)

    for attribute, value in attributes.items():
      self._output_writer.Write(u'\t')
      self._output_writer.Write(format_string.format(attribute, value))
      self._output_writer.Write(u'\n')

    if show_hex and file_entry:
      event_object.pathspec = file_entry.path_spec
      hexadecimal_output = self._GetEventDataHexDump(event_object)

      self.PrintHeader(u'Hexadecimal output from event.', character=u'-')
      self._output_writer.Write(hexadecimal_output)
      self._output_writer.Write(u'\n')

  def _PrintEventHeader(self, event_object, descriptions, exclude_timestamp):
    """Writes a list of strings that contains a header for the event.

    Args:
      event_object: event object (instance of event.EventObject).
      descriptions: list of strings describing the value of the header
                    timestamp.
      exclude_timestamp: boolean. If it is set to True the method
                         will not include the timestamp in the header.
    """
    format_string = self._GetFormatString(event_object)

    self._output_writer.Write(u'Key information.\n')
    if not exclude_timestamp:
      for description in descriptions:
        self._output_writer.Write(format_string.format(
            description, timelib.Timestamp.CopyToIsoFormat(
                event_object.timestamp)))
        self._output_writer.Write(u'\n')

    if hasattr(event_object, u'keyname'):
      self._output_writer.Write(
          format_string.format(u'Key Path', event_object.keyname))
      self._output_writer.Write(u'\n')

    if event_object.timestamp_desc != eventdata.EventTimestamp.WRITTEN_TIME:
      self._output_writer.Write(format_string.format(
          u'Description', event_object.timestamp_desc))
      self._output_writer.Write(u'\n')

    self.PrintHeader(u'Data', character=u'+')

  def _PrintEventObjectsBasedOnTime(
      self, event_objects, file_entry, show_hex=False):
    """Write extracted data from a list of event objects to an output writer.

    This function groups together a list of event objects based on timestamps.
    If more than one event are extracted with the same timestamp the timestamp
    itself is not repeated.

    Args:
      event_objects: list of event objects (instance of EventObject).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  Defaults to None.
      show_hex: optional boolean to indicate that the hexadecimal representation
                of the event should be included in the output. The default is
                False.
    """
    event_objects_and_timestamps = {}
    for event_object in event_objects:
      timestamp = event_object.timestamp
      _ = event_objects_and_timestamps.setdefault(timestamp, [])
      event_objects_and_timestamps[timestamp].append(event_object)

    list_of_timestamps = sorted(event_objects_and_timestamps.keys())

    if len(list_of_timestamps) > 1:
      exclude_timestamp_in_header = True
    else:
      exclude_timestamp_in_header = False

    first_timestamp = list_of_timestamps[0]
    first_event = event_objects_and_timestamps[first_timestamp][0]
    descriptions = set()
    for event_object in event_objects_and_timestamps[first_timestamp]:
      descriptions.add(getattr(event_object, u'timestamp_desc', u''))
    self._PrintEventHeader(
        first_event, list(descriptions), exclude_timestamp_in_header)

    for event_timestamp in list_of_timestamps:
      if exclude_timestamp_in_header:
        self._output_writer.Write(u'\n[{0:s}]\n'.format(
            timelib.Timestamp.CopyToIsoFormat(event_timestamp)))

      for event_object in event_objects_and_timestamps[event_timestamp]:
        self._PrintEventBody(
            event_object, file_entry=file_entry, show_hex=show_hex)

  def _PrintParsedRegistryFile(self, parsed_data, registry_helper):
    """Write extracted data from a Registry file to an output writer.

    Args:
      parsed_data: dict object returned from ParseRegisterFile.
      registry_helper: Registry file object (instance of PregRegistryHelper).
    """
    self.PrintHeader(u'Registry File', character=u'x')
    self._output_writer.Write(u'\n')
    self._output_writer.Write(
        u'{0:>15} : {1:s}\n'.format(u'Registry file', registry_helper.path))
    self._output_writer.Write(
        u'{0:>15} : {1:s}\n'.format(
            u'Registry file type', registry_helper.file_type))
    if registry_helper.collector_name:
      self._output_writer.Write(
          u'{0:>15} : {1:s}\n'.format(
              u'Registry Origin', registry_helper.collector_name))

    self._output_writer.Write(u'\n\n')

    for key_path, data in iter(parsed_data.items()):
      self._PrintParsedRegistryInformation(
          key_path, data, registry_helper.file_entry)

    self.PrintSeparatorLine()

  def _PrintParsedRegistryInformation(
      self, key_path, parsed_data, file_entry=None):
    """Write extracted data from a Registry key to an output writer.

    Args:
      key_path: path of the parsed Registry key.
      parsed_data: dict object returned from ParseRegisterFile.
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
    """
    registry_key = parsed_data.get(u'key', None)
    if registry_key:
      self._output_writer.Write(u'{0:>15} : {1:s}\n'.format(
          u'Key Name', key_path))
    elif not self._quiet:
      self._output_writer.Write(u'Unable to open key: {0:s}\n'.format(
          key_path))
      return
    else:
      return

    self._output_writer.Write(
        u'{0:>15} : {1:d}\n'.format(
            u'Subkeys', registry_key.number_of_subkeys))
    self._output_writer.Write(u'{0:>15} : {1:d}\n'.format(
        u'Values', registry_key.number_of_values))
    self._output_writer.Write(u'\n')

    if self._verbose_output:
      subkeys = parsed_data.get(u'subkeys', [])
      for subkey in subkeys:
        self._output_writer.Write(
            u'{0:>15} : {1:s}\n'.format(u'Key Name', subkey.path))

    key_data = parsed_data.get(u'data', None)
    if not key_data:
      return

    self.PrintParsedRegistryKey(
        key_data, file_entry=file_entry, show_hex=self._verbose_output)

  def _ScanFileSystem(self, path_resolver):
    """Scans a file system for the Windows volume.

    Args:
      path_resolver: the path resolver (instance of dfvfs.WindowsPathResolver).

    Returns:
      True if the Windows directory was found, False otherwise.
    """
    result = False

    for windows_path in self._WINDOWS_DIRECTORIES:
      windows_path_spec = path_resolver.ResolvePath(windows_path)

      result = windows_path_spec is not None
      if result:
        self._windows_directory = windows_path
        break

    return result

  def PrintHeader(self, text, character=u'*'):
    """Prints the header as a line with centered text.

    Args:
      text: The header text.
      character: Optional header line character. The default is '*'.
    """
    self._output_writer.Write(u'\n')

    format_string = u'{{0:{0:s}^{1:d}}}\n'.format(character, self._LINE_LENGTH)
    header_string = format_string.format(u' {0:s} '.format(text))
    self._output_writer.Write(header_string)

  def PrintParsedRegistryKey(self, key_data, file_entry=None, show_hex=False):
    """Write extracted data returned from ParseRegistryKey to an output writer.

    Args:
      key_data: dict object returned from ParseRegisterKey.
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      show_hex: optional boolean to indicate that the hexadecimal representation
                of the event should be included in the output. The default is
                False.
    """
    self.PrintHeader(u'Plugins', character=u'-')
    for plugin, event_objects in iter(key_data.items()):
      # TODO: make this a table view.
      self.PrintHeader(u'Plugin: {0:s}'.format(plugin.plugin_name))
      self._output_writer.Write(u'{0:s}\n'.format(plugin.DESCRIPTION))
      if plugin.URLS:
        self._output_writer.Write(
            u'Additional information can be found here:\n')

        for url in plugin.URLS:
          self._output_writer.Write(u'{0:>17s} {1:s}\n'.format(u'URL :', url))

      if not event_objects:
        continue

      self._PrintEventObjectsBasedOnTime(
          event_objects, file_entry, show_hex=show_hex)

    self.PrintSeparatorLine()
    self._output_writer.Write(u'\n\n')

  def GetWindowsRegistryPlugins(self):
    """Build a list of all available Windows Registry plugins.

    Returns:
      A plugins list (instance of PluginList).
    """
    return self._front_end.GetWindowsRegistryPlugins()

  def GetWindowsVolumeIdentifiers(self, scan_node, volume_identifiers):
    """Determines and returns back a list of Windows volume identifiers.

    Args:
      scan_node: the scan node (instance of dfvfs.ScanNode).
      volume_identifiers: list of allowed volume identifiers.

    Returns:
      A list of volume identifiers that have Windows partitions.
    """
    windows_volume_identifiers = []
    for sub_node in scan_node.sub_nodes:
      path_spec = getattr(sub_node, u'path_spec', None)
      if not path_spec:
        continue

      if path_spec.TYPE_INDICATOR != definitions.TYPE_INDICATOR_TSK_PARTITION:
        continue

      location = getattr(path_spec, u'location', u'')
      if not location:
        continue

      if location.startswith(u'/'):
        location = location[1:]

      if location not in volume_identifiers:
        continue

      selected_node = sub_node
      while selected_node.sub_nodes:
        selected_node = selected_node.sub_nodes[0]

      file_system = resolver.Resolver.OpenFileSystem(selected_node.path_spec)
      path_resolver = windows_path_resolver.WindowsPathResolver(
          file_system, selected_node.path_spec)

      if self._ScanFileSystem(path_resolver):
        windows_volume_identifiers.append(location)

    return windows_volume_identifiers

  def ListPluginInformation(self):
    """Lists Registry plugin information."""
    table_view = cli_views.CLITableView(title=u'Supported Plugins')
    plugin_list = self._front_end.registry_plugin_list
    for plugin_class in plugin_list.GetAllPlugins():
      table_view.AddRow([plugin_class.NAME, plugin_class.DESCRIPTION])
    table_view.Write(self._output_writer)

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      A boolean value indicating the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)

    additional_options = argument_parser.add_argument_group(
        u'Additional Options')

    additional_options.add_argument(
        u'-r', u'--restore-points', u'--restore_points',
        dest=u'restore_points', action=u'store_true', default=False,
        help=u'Include restore points in the Registry file locations.')

    self.AddVSSProcessingOptions(additional_options)

    image_options = argument_parser.add_argument_group(u'Image Options')

    image_options.add_argument(
        u'-i', u'--image', dest=u'image', action=u'store', type=unicode,
        default=u'', metavar=u'IMAGE_PATH', help=(
            u'If the Registry file is contained within a storage media image, '
            u'set this option to specify the path of image file.'))

    self.AddStorageMediaImageOptions(image_options)

    info_options = argument_parser.add_argument_group(u'Informational Options')

    info_options.add_argument(
        u'--info', dest=u'show_info', action=u'store_true', default=False,
        help=u'Print out information about supported plugins.')

    info_options.add_argument(
        u'-v', u'--verbose', dest=u'verbose', action=u'store_true',
        default=False, help=u'Print sub key information.')

    info_options.add_argument(
        u'-q', u'--quiet', dest=u'quiet', action=u'store_true', default=False,
        help=u'Do not print out key names that the tool was unable to open.')

    mode_options = argument_parser.add_argument_group(u'Run Mode Options')

    mode_options.add_argument(
        u'-c', u'--console', dest=u'console', action=u'store_true',
        default=False, help=(
            u'Drop into a console session Instead of printing output '
            u'to STDOUT.'))

    mode_options.add_argument(
        u'-k', u'--key', dest=u'key', action=u'store', default=u'',
        type=unicode, metavar=u'REGISTRY_KEYPATH', help=(
            u'A Registry key path that the tool should parse using all '
            u'available plugins.'))

    mode_options.add_argument(
        u'-p', u'--plugins', dest=u'plugin_names', action=u'append', default=[],
        type=unicode, metavar=u'PLUGIN_NAME',
        help=(
            u'Substring match of the Registry plugin to be used, this '
            u'parameter can be repeated to create a list of plugins to be '
            u'run against, eg: "-p userassist -p rdp" or "-p userassist".'))

    argument_parser.add_argument(
        u'registry_file', action=u'store', metavar=u'REGHIVE', nargs=u'?',
        help=(
            u'The Registry hive to read key from (not needed if running '
            u'using a plugin)'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())
      self._output_writer.Write(u'\n')
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      logging.error(u'{0:s}'.format(exception))

      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())
      self._output_writer.Write(u'\n')

      return False

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    if getattr(options, u'show_info', False):
      self.run_mode = self.RUN_MODE_LIST_PLUGINS
      return

    registry_file = getattr(options, u'registry_file', None)
    image = getattr(options, u'image', None)
    source_path = None
    if image:
      # TODO: refactor, there should be no need for separate code paths.
      super(PregTool, self).ParseOptions(options)
      source_path = image
      self._front_end.SetSingleFile(False)
    else:
      self._ParseInformationalOptions(options)
      source_path = registry_file
      self._front_end.SetSingleFile(True)

    if source_path is None:
      raise errors.BadConfigOption(u'No source path set.')

    self._front_end.SetSourcePath(source_path)
    self._source_path = os.path.abspath(source_path)

    if not image and not registry_file:
      raise errors.BadConfigOption(u'Not enough parameters to proceed.')

    if registry_file:
      if not image and not os.path.isfile(registry_file):
        raise errors.BadConfigOption(
            u'Registry file: {0:s} does not exist.'.format(registry_file))

    self._key_path = getattr(options, u'key', None)
    self._parse_restore_points = getattr(options, u'restore_points', False)

    self._quiet = getattr(options, u'quiet', False)

    self._verbose_output = getattr(options, u'verbose', False)

    if image:
      file_to_check = image
    else:
      file_to_check = registry_file

    is_file, reason = self._PathExists(file_to_check)
    if not is_file:
      raise errors.BadConfigOption(
          u'Unable to read the input file with error: {0:s}'.format(reason))

    self.plugin_names = getattr(options, u'plugin_names', [])

    self._front_end.SetKnowledgeBase(self._knowledge_base_object)

    if getattr(options, u'console', False):
      self.run_mode = self.RUN_MODE_CONSOLE
    elif getattr(options, u'key', u'') and registry_file:
      self.run_mode = self.RUN_MODE_REG_KEY
    elif self.plugin_names:
      self.run_mode = self.RUN_MODE_REG_PLUGIN
    elif registry_file:
      self.run_mode = self.RUN_MODE_REG_FILE
    else:
      raise errors.BadConfigOption(
          u'Incorrect usage. You\'ll need to define the path of either '
          u'a storage media image or a Windows Registry file.')

    self.registry_file = registry_file

    scan_context = self.ScanSource()
    self.source_type = scan_context.source_type
    self._front_end.SetSourcePathSpecs(self._source_path_specs)

  def RunModeRegistryFile(self):
    """Run against a Registry file.

    Finds and opens all Registry hives as configured in the configuration
    object and determines the type of Registry file opened. Then it will
    load up all the Registry plugins suitable for that particular Registry
    file, find all Registry keys they are able to parse and run through
    them, one by one.
    """
    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_file_types=[self.registry_file])

    for registry_helper in registry_helpers:
      try:
        registry_helper.Open()

        self._PrintParsedRegistryFile({}, registry_helper)
        plugins_to_run = self._front_end.GetRegistryPluginsFromRegistryType(
            registry_helper.file_type)

        for plugin in plugins_to_run:
          key_paths = plugin.GetKeyPaths()
          self._front_end.ExpandKeysRedirect(key_paths)
          for key_path in key_paths:
            key = registry_helper.GetKeyByPath(key_path)
            if not key:
              continue
            parsed_data = self._front_end.ParseRegistryKey(
                key, registry_helper, use_plugins=[plugin.NAME])
            self.PrintParsedRegistryKey(
                parsed_data, file_entry=registry_helper.file_entry,
                show_hex=self._verbose_output)
      finally:
        registry_helper.Close()
        self.PrintSeparatorLine()

  def RunModeRegistryKey(self):
    """Run against a specific Registry key.

    Finds and opens all Registry hives as configured in the configuration
    object and tries to open the Registry key that is stored in the
    configuration object for every detected hive file and parses it using
    all available plugins.
    """
    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_file_types=[self.registry_file],
        plugin_names=self.plugin_names)

    key_paths = [self._key_path]

    # Expand the keys paths if there is a need (due to Windows redirect).
    self._front_end.ExpandKeysRedirect(key_paths)

    for registry_helper in registry_helpers:
      parsed_data = self._front_end.ParseRegistryFile(
          registry_helper, key_paths=key_paths)
      self._PrintParsedRegistryFile(parsed_data, registry_helper)

  def RunModeRegistryPlugin(self):
    """Run against a set of Registry plugins."""
    # TODO: Add support for splitting the output to separate files based on
    # each plugin name.
    registry_helpers = self._front_end.GetRegistryHelpers(
        plugin_names=self.plugin_names)

    plugins = []
    for plugin_name in self.plugin_names:
      plugins.extend(self._front_end.GetRegistryPlugins(plugin_name))
    plugin_list = [plugin.NAME for plugin in plugins]

    # In order to get all the Registry keys we need to expand them.
    if not registry_helpers:
      return

    registry_helper = registry_helpers[0]
    key_paths = []
    plugins_list = self._front_end.registry_plugin_list
    try:
      registry_helper.Open()

      # Get all the appropriate keys from these plugins.
      key_paths = plugins_list.GetKeyPaths(plugin_names=plugin_list)

    finally:
      registry_helper.Close()

    for registry_helper in registry_helpers:
      parsed_data = self._front_end.ParseRegistryFile(
          registry_helper, key_paths=key_paths, use_plugins=plugin_list)
      self._PrintParsedRegistryFile(parsed_data, registry_helper)


@magic.magics_class
class PregMagics(magic.Magics):
  """Class that implements the iPython console magic functions."""

  # Needed to give the magic class access to the front end tool
  # for processing and formatting.
  console = None

  EXPANSION_KEY_OPEN = r'{'
  EXPANSION_KEY_CLOSE = r'}'

  # Match against one instance, not two of the expansion key.
  EXPANSION_RE = re.compile(r'{0:s}{{1}}[^{1:s}]+?{1:s}'.format(
      EXPANSION_KEY_OPEN, EXPANSION_KEY_CLOSE))

  REGISTRY_KEY_PATH_SEPARATOR = u'\\'
  REGISTRY_FILE_BASE_PATH = u'\\'

  # TODO: Use the output writer from the tool.
  output_writer = cli_tools.StdoutOutputWriter()

  def _HiveActionList(self, unused_line):
    """Handles the hive list action.

    Args:
      line: the command line provide via the console.
    """
    self.console.PrintRegistryFileList()
    self.output_writer.Write(u'\n')
    self.output_writer.Write(
        u'To open a Registry file, use: hive open INDEX\n')

  def _HiveActionOpen(self, line):
    """Handles the hive open action.

    Args:
      line: the command line provide via the console.
    """
    try:
      registry_file_index = int(line[5:], 10)
    except ValueError:
      self.output_writer.Write(
          u'Unable to open Registry file, invalid index number.\n')
      return

    try:
      self.console.LoadRegistryFile(registry_file_index)
    except errors.UnableToLoadRegistryHelper as exception:
      self.output_writer.Write(
          u'Unable to load hive, with error: {0:s}.\n'.format(exception))
      return

    registry_helper = self.console.current_helper
    self.output_writer.Write(u'Opening hive: {0:s} [{1:s}]\n'.format(
        registry_helper.path, registry_helper.collector_name))
    self.console.SetPrompt(registry_file_path=registry_helper.path)

  def _HiveActionScan(self, line):
    """Handles the hive scan action.

    Args:
      line: the command line provide via the console.
    """
    # Line contains: "scan REGISTRY_TYPES" where REGISTRY_TYPES is a comma
    # separated list.
    registry_file_type_string = line[5:]
    if not registry_file_type_string:
      registry_file_types = self.console.preg_front_end.GetRegistryTypes()
    else:
      registry_file_types = [
          string.strip() for string in registry_file_type_string.split(u',')]

    registry_helpers = self.console.preg_front_end.GetRegistryHelpers(
        registry_file_types=registry_file_types)

    for registry_helper in registry_helpers:
      self.console.AddRegistryHelper(registry_helper)

    self.console.PrintRegistryFileList()

  @magic.line_magic(u'cd')
  def ChangeDirectory(self, key_path):
    """Change between Registry keys, like a directory tree.

    The key path can either be an absolute path or a relative one.
    Absolute paths can use '.' and '..' to denote current and parent
    directory/key path. If no key path is set the current key is changed
    to point to the root key.

    Args:
      key_path: path to the key to traverse to.
    """
    if not self.console and not self.console.IsLoaded():
      return

    registry_helper = self.console.current_helper
    if not registry_helper:
      return

    if not key_path:
      key_path = self.REGISTRY_FILE_BASE_PATH

    key_path_upper = key_path.upper()

    # Check if we need to expand environment attributes.
    match = self.EXPANSION_RE.search(key_path)
    if match and u'{0:s}{0:s}'.format(
        self.EXPANSION_KEY_OPEN) not in match.group(0):
      pre_obj = self.console.preg_front_end.knowledge_base_object.pre_obj

      # TODO: deprecate usage of pre_obj.
      path_attributes = pre_obj.__dict__

      try:
        # TODO: create an ExpandKeyPath function.
        key_path = registry_helper._win_registry.ExpandKeyPath(
            key_path, path_attributes)
      except (KeyError, IndexError):
        pass

    registry_key = None
    relative_key_path = key_path
    if (key_path.startswith(self.REGISTRY_KEY_PATH_SEPARATOR) or
        key_path_upper.startswith(u'HKEY_')):
      registry_key = registry_helper.GetKeyByPath(key_path)

    elif key_path == u'.':
      return

    elif key_path.startswith(u'.\\'):
      current_path = registry_helper.GetCurrentRegistryPath()
      _, _, relative_key_path = key_path.partition(
          self.REGISTRY_KEY_PATH_SEPARATOR)
      registry_key = registry_helper.GetKeyByPath(u'{0:s}\\{1:s}'.format(
          current_path, relative_key_path))

    elif key_path.startswith(u'..'):
      parent_path, _, _ = registry_helper.GetCurrentRegistryPath().rpartition(
          self.REGISTRY_KEY_PATH_SEPARATOR)
      # We know the path starts with a "..".
      if len(key_path) == 2:
        relative_key_path = u''
      else:
        relative_key_path = key_path[3:]

      if parent_path:
        if relative_key_path:
          path = u'{0:s}\\{1:s}'.format(parent_path, relative_key_path)
        else:
          path = parent_path
        registry_key = registry_helper.GetKeyByPath(path)
      else:
        registry_key = registry_helper.GetKeyByPath(
            u'\\{0:s}'.format(relative_key_path))

    else:
      # Check if key is not set at all, then assume traversal from root.
      if not registry_helper.GetCurrentRegistryPath():
        _ = registry_helper.GetKeyByPath(self.REGISTRY_FILE_BASE_PATH)

      current_key = registry_helper.GetCurrentRegistryKey()
      if (not current_key or (
          registry_helper.root_key and
          current_key.name == registry_helper.root_key.name)):
        relative_key_path = u'\\{0:s}'.format(key_path)
      else:
        relative_key_path = u'{0:s}\\{1:s}'.format(current_key.path, key_path)
      registry_key = registry_helper.GetKeyByPath(relative_key_path)

    if not registry_key:
      self.output_writer.Write(
          u'Unable to change to: {0:s}\n'.format(relative_key_path))
      return

    if relative_key_path == self.REGISTRY_FILE_BASE_PATH:
      path = self.REGISTRY_FILE_BASE_PATH
    else:
      path = registry_key.path

    sanitized_path = path.replace(u'}', u'}}').replace(u'{', u'{{')
    sanitized_path = sanitized_path.replace(
        self.REGISTRY_KEY_PATH_SEPARATOR, u'\\\\')
    self.console.SetPrompt(
        registry_file_path=registry_helper.path,
        prepend_string=sanitized_path)

  @magic.line_magic(u'hive')
  def HiveActions(self, line):
    """Handles the hive actions.

    Args:
      line: the command line provide via the console.
    """
    if line.startswith(u'list'):
      self._HiveActionList(line)

    elif line.startswith(u'open ') or line.startswith(u'load '):
      self._HiveActionOpen(line)

    elif line.startswith(u'scan'):
      self._HiveActionScan(line)

  @magic.line_magic(u'ls')
  def ListDirectoryContent(self, line):
    """List all subkeys and values of the current key."""
    if not self.console and not self.console.IsLoaded():
      return

    if u'true' in line.lower():
      verbose = True
    elif u'-v' in line.lower():
      verbose = True
    else:
      verbose = False

    sub = []
    current_file = self.console.current_helper
    if not current_file:
      return

    current_key = current_file.GetCurrentRegistryKey()
    for key in current_key.GetSubkeys():
      # TODO: move this construction into a separate function in OutputWriter.
      time_string = timelib.Timestamp.CopyToIsoFormat(
          key.last_written_timestamp)
      time_string, _, _ = time_string.partition(u'.')

      sub.append((u'{0:>19s} {1:>15s}  {2:s}'.format(
          time_string.replace(u'T', u' '), u'[KEY]',
          key.name), True))

    for value in current_key.GetValues():
      if not verbose:
        sub.append((u'{0:>19s} {1:>14s}]  {2:s}'.format(
            u'', u'[' + value.data_type_string, value.name), False))
      else:
        if value.DataIsString():
          value_string = u'{0:s}'.format(value.data)
        elif value.DataIsInteger():
          value_string = u'{0:d}'.format(value.data)
        elif value.DataIsMultiString():
          value_string = u'{0:s}'.format(u''.join(value.data))
        elif value.DataIsBinaryData():
          value_string = hexdump.Hexdump.FormatData(
              value.data, maximum_data_size=16)
        else:
          value_string = u''

        sub.append((
            u'{0:>19s} {1:>14s}]  {2:<25s}  {3:s}'.format(
                u'', u'[' + value.data_type_string, value.name, value_string),
            False))

    for entry, subkey in sorted(sub):
      if subkey:
        self.output_writer.Write(u'dr-xr-xr-x {0:s}\n'.format(entry))
      else:
        self.output_writer.Write(u'-r-xr-xr-x {0:s}\n'.format(entry))

  @magic.line_magic(u'parse')
  def ParseCurrentKey(self, line):
    """Parse the current key."""
    if not self.console and not self.console.IsLoaded():
      return

    if u'true' in line.lower():
      verbose = True
    elif u'-v' in line.lower():
      verbose = True
    else:
      verbose = False

    current_helper = self.console.current_helper
    if not current_helper:
      return

    current_key = current_helper.GetCurrentRegistryKey()
    parsed_data = self.console.preg_front_end.ParseRegistryKey(
        current_key, current_helper)

    self.console.preg_tool.PrintParsedRegistryKey(
        parsed_data, file_entry=current_helper.file_entry, show_hex=verbose)

    # Print a hexadecimal representation of all binary values.
    if verbose:
      header_shown = False
      for value in current_helper.GetCurrentRegistryKey().GetValues():
        if not value.DataIsBinaryData():
          continue

        if not header_shown:
          table_view = cli_views.CLITableView(
              title=u'Hexadecimal representation')
          header_shown = True
        else:
          table_view = cli_views.CLITableView()

        table_view.AddRow([u'Attribute', value.name])
        table_view.Write(self.output_writer)

        self.console.preg_tool.PrintSeparatorLine()
        self.console.preg_tool.PrintSeparatorLine()

        value_string = hexdump.Hexdump.FormatData(value.data)
        self.output_writer.Write(value_string)
        self.output_writer.Write(u'\n')
        self.output_writer.Write(u'+-'*40)
        self.output_writer.Write(u'\n')

  def _PrintPluginHelp(self, plugin_object):
    """Prints the help information of a plugin.

    Args:
      plugin_object: a Windows Registry plugin object (instance of
                     WindowsRegistryPlugin).
    """
    table_view = cli_views.CLITableView(title=plugin_object.NAME)

    # TODO: replace __doc__ by DESCRIPTION.
    description = plugin_object.__doc__
    table_view.AddRow([u'Description', description])
    self.output_writer.Write(u'\n')

    for registry_key in plugin_object.expanded_keys:
      table_view.AddRow([u'Registry Key', registry_key])
    table_view.Write(self._output_writer)

  @magic.line_magic(u'plugin')
  def ParseWithPlugin(self, line):
    """Parse a Registry key using a specific plugin."""
    if not self.console and not self.console.IsLoaded():
      self._output_writer.Write(u'No hive loaded, unable to parse.\n')
      return

    current_helper = self.console.current_helper
    if not current_helper:
      return

    if not line:
      self.output_writer.Write(u'No plugin name added.\n')
      return

    plugin_name = line
    if u'-h' in line:
      items = line.split()
      if len(items) != 2:
        self.output_writer.Write(u'Wrong usage: plugin [-h] PluginName\n')
        return
      if items[0] == u'-h':
        plugin_name = items[1]
      else:
        plugin_name = items[0]

    registry_file_type = current_helper.file_type
    plugins_list = self.console.preg_tool.GetWindowsRegistryPlugins()
    plugin_object = plugins_list.GetPluginObjectByName(
        registry_file_type, plugin_name)
    if not plugin_object:
      self.output_writer.Write(
          u'No plugin named: {0:s} available for Registry type {1:s}\n'.format(
              plugin_name, registry_file_type))
      return

    key_paths = plugin_object.GetKeyPaths()
    if not key_paths:
      self.output_writer.Write(
          u'Plugin: {0:s} has no key information.\n'.format(line))
      return

    if u'-h' in line:
      self._PrintPluginHelp(plugin_object)
      return

    for key_path in key_paths:
      registry_key = current_helper.GetKeyByPath(key_path)
      if not registry_key:
        self.output_writer.Write(u'Key: {0:s} not found\n'.format(key_path))
        continue

      # Move the current location to the key to be parsed.
      self.ChangeDirectory(key_path)
      # Parse the key.
      current_key = current_helper.GetCurrentRegistryKey()
      parsed_data = self.console.preg_front_end.ParseRegistryKey(
          current_key, current_helper, use_plugins=[plugin_name])
      self.console.preg_tool.PrintParsedRegistryKey(
          parsed_data, file_entry=current_helper.file_entry)

  @magic.line_magic(u'pwd')
  def PrintCurrentWorkingDirectory(self, unused_line):
    """Print the current path."""
    if not self.console and not self.console.IsLoaded():
      return

    current_helper = self.console.current_helper
    if not current_helper:
      return

    self.output_writer.Write(u'{0:s}\n'.format(
        current_helper.GetCurrentRegistryPath()))


class PregConsole(object):
  """Class that implements the preg iPython console."""

  _BASE_FUNCTIONS = [
      (u'cd key', u'Navigate the Registry like a directory structure.'),
      (u'ls [-v]', (
          u'List all subkeys and values of a Registry key. If called as ls '
          u'True then values of keys will be included in the output.')),
      (u'parse -[v]', u'Parse the current key using all plugins.'),
      (u'plugin [-h] plugin_name', (
          u'Run a particular key-based plugin on the loaded hive. The correct '
          u'Registry key will be loaded, opened and then parsed.')),
      (u'get_value value_name', (
          u'Get a value from the currently loaded Registry key.')),
      (u'get_value_data value_name', (
          u'Get a value data from a value stored in the currently loaded '
          u'Registry key.')),
      (u'get_key', u'Return the currently loaded Registry key.')]

  @property
  def current_helper(self):
    """The currently loaded Registry helper."""
    return self._currently_registry_helper

  def __init__(self, preg_tool):
    """Initialize the console object.

    Args:
      preg_tool: a preg tool object (instance of PregTool).
    """
    super(PregConsole, self).__init__()
    self._currently_registry_helper = None
    self._currently_loaded_helper_path = u''
    self._registry_helpers = {}

    preferred_encoding = locale.getpreferredencoding()
    if not preferred_encoding:
      preferred_encoding = u'utf-8'

    # TODO: Make this configurable, or derive it from the tool.
    self._output_writer = cli_tools.StdoutOutputWriter(
        encoding=preferred_encoding)

    self.preg_tool = preg_tool
    self.preg_front_end = getattr(preg_tool, u'_front_end', None)

    self.parser_mediator = self.preg_front_end.CreateParserMediator()

  def _CommandGetCurrentKey(self):
    """Command function to retrieve the currently loaded Registry key.

    Returns:
      The currently loaded Registry key (instance of dfwinreg.WinRegistryKey)
      or None if there is no loaded key.
    """
    registry_helper = self._currently_registry_helper
    return registry_helper.GetCurrentRegistryKey()

  def _CommandGetValue(self, value_name):
    """Return a value object from the currently loaded Registry key.

    Args:
      value_name: string containing the name of the value to be retrieved.

    Returns:
      The Registry value (instance of dfwinreg.WinRegistryValue) if it exists,
      None if either there is no currently loaded Registry key or if the value
      does not exist.
    """
    registry_helper = self._currently_registry_helper

    current_key = registry_helper.GetCurrentRegistryKey()
    if not current_key:
      return

    return current_key.GetValueByName(value_name)

  def _CommandGetValueData(self, value_name):
    """Return the value data from a value in the currently loaded Registry key.

    Args:
      value_name: string containing the name of the value to be retrieved.

    Returns:
      The data from a Registry value if it exists, None if either there is no
      currently loaded Registry key or if the value does not exist.
    """
    value = self._CommandGetValue(value_name)
    if not value:
      return

    return value.data

  def _CommandGetRangeForAllLoadedHives(self):
    """Return a range or a list of all loaded hives."""
    return range(0, self._CommandGetTotalNumberOfLoadedHives())

  def _CommandGetTotalNumberOfLoadedHives(self):
    """Return the total number of Registry hives that are loaded."""
    return len(self._registry_helpers)

  def AddRegistryHelper(self, registry_helper):
    """Add a Registry helper to the console object.

    Args:
      registry_helper: registry helper object (instance of PregRegistryHelper)

    Raises:
      ValueError: if not Registry helper is supplied or Registry helper is not
                  the correct object (instance of PregRegistryHelper).
    """
    if not registry_helper:
      raise ValueError(u'No Registry helper supplied.')

    if not isinstance(registry_helper, preg.PregRegistryHelper):
      raise ValueError(
          u'Object passed in is not an instance of PregRegistryHelper.')

    if registry_helper.path not in self._registry_helpers:
      self._registry_helpers[registry_helper.path] = registry_helper

  def GetConfig(self):
    """Retrieves the iPython config.

    Returns:
      The IPython config object (instance of
      IPython.terminal.embed.InteractiveShellEmbed)
    """
    try:
      # The "get_ipython" function does not exist except within an IPython
      # session.
      return get_ipython()  # pylint: disable=undefined-variable
    except NameError:
      return Config()

  def IsLoaded(self):
    """Checks if a Windows Registry file is loaded.

    Returns:
      True if a Registry helper is currently loaded and ready
      to be used, otherwise False is returned.
    """
    registry_helper = self._currently_registry_helper
    if not registry_helper:
      return False

    current_key = registry_helper.GetCurrentRegistryKey()
    if hasattr(current_key, u'path'):
      return True

    if registry_helper.name != u'N/A':
      return True

    self._output_writer.Write(
        u'No hive loaded, cannot complete action. Use "hive list" '
        u'and "hive open" to load a hive.\n')
    return False

  def PrintBanner(self):
    """Writes a banner to the output writer."""
    self._output_writer.Write(u'\n')
    self._output_writer.Write(
        u'Welcome to PREG - home of the Plaso Windows Registry Parsing.\n')

    table_view = cli_views.CLITableView(
        column_names=[u'Function', u'Description'], title=u'Available commands')
    for function_name, description in self._BASE_FUNCTIONS:
      table_view.AddRow([function_name, description])
    table_view.Write(self._output_writer)

    if len(self._registry_helpers) == 1:
      self.LoadRegistryFile(0)
      registry_helper = self._currently_registry_helper
      self._output_writer.Write(
          u'Opening hive: {0:s} [{1:s}]\n'.format(
              registry_helper.path, registry_helper.collector_name))
      self.SetPrompt(registry_file_path=registry_helper.path)

    # TODO: make sure to limit number of characters per line of output.
    registry_helper = self._currently_registry_helper
    if registry_helper and registry_helper.name != u'N/A':
      self._output_writer.Write(
          u'Registry file: {0:s} [{1:s}] is available and loaded.\n'.format(
              registry_helper.name, registry_helper.path))

    else:
      self._output_writer.Write(u'More than one Registry file ready for use.\n')
      self._output_writer.Write(u'\n')
      self.PrintRegistryFileList()
      self._output_writer.Write(u'\n')
      self._output_writer.Write((
          u'Use "hive open INDEX" to load a Registry file and "hive list" to '
          u'see a list of available Registry files.\n'))

    self._output_writer.Write(u'\nHappy command line console fu-ing.')

  def LoadRegistryFile(self, index):
    """Load a Registry file helper from the list of Registry file helpers.

    Args:
      index: index into the list of available Registry helpers.

    Raises:
      UnableToLoadRegistryHelper: if the index attempts to load an entry
                                  that does not exist or if there are no
                                  Registry helpers loaded.
    """
    helper_keys = self._registry_helpers.keys()

    if not helper_keys:
      raise errors.UnableToLoadRegistryHelper(u'No Registry helpers loaded.')

    if index < 0 or index >= len(helper_keys):
      raise errors.UnableToLoadRegistryHelper(u'Index out of bounds.')

    if self._currently_registry_helper:
      self._currently_registry_helper.Close()

    registry_helper_path = helper_keys[index]
    self._currently_registry_helper = (
        self._registry_helpers[registry_helper_path])
    self._currently_loaded_helper_path = registry_helper_path

    self._currently_registry_helper.Open()

  def PrintRegistryFileList(self):
    """Write a list of all available registry helpers to an output writer."""
    if not self._registry_helpers:
      return

    self._output_writer.Write(u'Index Hive [collector]\n')
    for index, registry_helper in enumerate(self._registry_helpers.values()):
      collector_name = registry_helper.collector_name
      if not collector_name:
        collector_name = u'Currently Allocated'

      if self._currently_loaded_helper_path == registry_helper.path:
        star = u'*'
      else:
        star = u''

      self._output_writer.Write(u'{0:<5d} {1:s}{2:s} [{3:s}]\n'.format(
          index, star, registry_helper.path, collector_name))

  def SetPrompt(
      self, registry_file_path=None, config=None, prepend_string=None):
    """Sets the prompt string on the console.

    Args:
      registry_file_path: optional hive name or path of the Registry file. The
                          default is None which sets the value to a string
                          indicating an unknown Registry file.
      config: optional IPython configuration object (instance of
              IPython.terminal.embed.InteractiveShellEmbed). The default is None
              and an attempt to automatically derive the config is done.
      prepend_string: optional string that can be injected into the prompt
                      just prior to the command count. The default is None.
    """
    if registry_file_path is None:
      path_string = u'Unknown Registry file loaded'
    else:
      path_string = registry_file_path

    prompt_strings = [
        r'[{color.LightBlue}\T{color.Normal}]',
        r'{color.LightPurple} ',
        path_string,
        r'\n{color.Normal}']
    if prepend_string is not None:
      prompt_strings.append(u'{0:s} '.format(prepend_string))
    prompt_strings.append(r'[{color.Red}\#{color.Normal}] \$ ')

    if config is None:
      ipython_config = self.GetConfig()
    else:
      ipython_config = config

    try:
      ipython_config.PromptManager.in_template = r''.join(prompt_strings)
    except AttributeError:
      ipython_config.prompt_manager.in_template = r''.join(prompt_strings)

  def Run(self):
    """Runs the interactive console."""
    source_type = self.preg_tool.source_type
    if source_type == source_scanner.SourceScannerContext.SOURCE_TYPE_FILE:
      registry_file_types = []
    elif self.preg_tool.registry_file:
      registry_file_types = [self.preg_tool.registry_file]
    else:
      # No Registry type specified use all available types instead.
      registry_file_types = self.preg_front_end.GetRegistryTypes()

    registry_helpers = self.preg_front_end.GetRegistryHelpers(
        registry_file_types=registry_file_types,
        plugin_names=self.preg_tool.plugin_names)

    for registry_helper in registry_helpers:
      self.AddRegistryHelper(registry_helper)

    # Adding variables in scope.
    namespace = {}

    namespace.update(globals())
    namespace.update({
        u'console': self,
        u'front_end': self.preg_front_end,
        u'get_current_key': self._CommandGetCurrentKey,
        u'get_key': self._CommandGetCurrentKey,
        u'get_value': self. _CommandGetValue,
        u'get_value_data': self. _CommandGetValueData,
        u'number_of_hives': self._CommandGetTotalNumberOfLoadedHives,
        u'range_of_hives': self._CommandGetRangeForAllLoadedHives,
        u'tool': self.preg_tool})

    ipshell_config = self.GetConfig()

    if len(self._registry_helpers) == 1:
      self.LoadRegistryFile(0)

    registry_helper = self._currently_registry_helper

    if registry_helper:
      registry_file_path = registry_helper.name
    else:
      registry_file_path = u'NO HIVE LOADED'

    self.SetPrompt(registry_file_path=registry_file_path, config=ipshell_config)

    # Starting the shell.
    ipshell = InteractiveShellEmbed(
        user_ns=namespace, config=ipshell_config, banner1=u'', exit_msg=u'')
    ipshell.confirm_exit = False

    self.PrintBanner()

    # Adding "magic" functions.
    ipshell.register_magics(PregMagics)
    PregMagics.console = self

    # Set autocall to two, making parenthesis not necessary when calling
    # function names (although they can be used and are necessary sometimes,
    # like in variable assignments, etc).
    ipshell.autocall = 2

    # Registering command completion for the magic commands.
    ipshell.set_hook(
        u'complete_command', CommandCompleterCd, str_key=u'%cd')
    ipshell.set_hook(
        u'complete_command', CommandCompleterVerbose, str_key=u'%ls')
    ipshell.set_hook(
        u'complete_command', CommandCompleterVerbose, str_key=u'%parse')
    ipshell.set_hook(
        u'complete_command', CommandCompleterPlugins, str_key=u'%plugin')

    ipshell()


# Completer commands need to be top level methods or directly callable
# and cannot be part of a class that needs to be initialized.
def CommandCompleterCd(console, unused_core_completer):
  """Command completer function for cd.

  Args:
    console: IPython shell object (instance of InteractiveShellEmbed).
  """
  return_list = []

  namespace = getattr(console, u'user_ns', {})
  magic_class = namespace.get(u'PregMagics', None)

  if not magic_class:
    return return_list

  if not magic_class.console.IsLoaded():
    return return_list

  registry_helper = magic_class.console.current_helper
  current_key = registry_helper.GetCurrentRegistryKey()
  for key in current_key.GetSubkeys():
    return_list.append(key.name)

  return return_list


# Completer commands need to be top level methods or directly callable
# and cannot be part of a class that needs to be initialized.
def CommandCompleterPlugins(console, core_completer):
  """Command completer function for plugins.

  Args:
    console: IPython shell object (instance of InteractiveShellEmbed).
    core_completer: IPython completer object (instance of completer.Bunch).

  Returns:
    A list of command options.
  """
  namespace = getattr(console, u'user_ns', {})
  magic_class = namespace.get(u'PregMagics', None)

  if not magic_class:
    return []

  if not magic_class.console.IsLoaded():
    return []

  command_options = []
  if not u'-h' in core_completer.line:
    command_options.append(u'-h')

  registry_helper = magic_class.console.current_helper
  registry_file_type = registry_helper.file_type

  plugins_list = console.preg_tool.GetWindowsRegistryPlugins()
  # TODO: refactor this into PluginsList.
  for plugin_cls in plugins_list.GetKeyPlugins(registry_file_type):
    if plugin_cls.NAME == u'winreg_default':
      continue
    command_options.append(plugin_cls.NAME)

  return command_options


# Completer commands need to be top level methods or directly callable
# and cannot be part of a class that needs to be initialized.
def CommandCompleterVerbose(unused_console, core_completer):
  """Command completer function for verbose output.

  Args:
    core_completer: IPython completer object (instance of completer.Bunch).

  Returns:
    A list of command options.
  """
  if u'-v' in core_completer.line:
    return []

  return [u'-v']


def Main():
  """Run the tool."""
  tool = PregTool()

  if not tool.ParseArguments():
    return False

  if tool.run_mode == tool.RUN_MODE_LIST_PLUGINS:
    tool.ListPluginInformation()
  elif tool.run_mode == tool.RUN_MODE_REG_KEY:
    tool.RunModeRegistryKey()
  elif tool.run_mode == tool.RUN_MODE_REG_PLUGIN:
    tool.RunModeRegistryPlugin()
  elif tool.run_mode == tool.RUN_MODE_REG_FILE:
    tool.RunModeRegistryFile()
  elif tool.run_mode == tool.RUN_MODE_CONSOLE:
    preg_console = PregConsole(tool)
    preg_console.Run()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
