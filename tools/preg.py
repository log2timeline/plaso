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
import binascii
import logging
import os
import re
import sys
import textwrap

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

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

# Import the winreg formatter to register it, adding the option
# to print event objects using the default formatter.
# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter

from plaso.cli import storage_media_tool
from plaso.cli import tools as cli_tools
# TODO: move queue and single_process into front end.
from plaso.engine import queue
from plaso.engine import single_process
from plaso.frontend import frontend
from plaso.frontend import preg
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import manager as parsers_manager
from plaso.parsers import winreg as winreg_parser
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager
from plaso.winreg import cache
from plaso.winreg import path_expander as winreg_path_expander
from plaso.winreg import winregistry


# Older versions of IPython don't have a version_info attribute.
if getattr(IPython, 'version_info', (0, 0, 0)) < (1, 2, 1):
  raise ImportWarning(
      'Preg requires at least IPython version 1.2.1.')


# TODO: replace by tool.PrintHeader.
def FormatHeader(header, char='*'):
  """Formats the header as a line of 80 chars with the header text centered."""
  format_string = '\n{{0:{0:s}^80}}'.format(char)
  return format_string.format(u' {0:s} '.format(header))


# TODO: replace by tool.PrintColumnValue.
def FormatOutputString(name, description, col_length=25):
  """Return a formatted string ready for output."""
  max_width = 80
  line_length = max_width - col_length - 3

  # TODO: add an explanation what this code is doing.
  fmt = u'{{:>{0:d}s}} : {{}}'.format(col_length)
  fmt_second = u'{{:<{0:d}}}{{}}'.format(col_length + 3)

  description = unicode(description)
  if len(description) < line_length:
    return fmt.format(name, description)

  # Split each word up in the description.
  words = description.split()

  current = 0

  lines = []
  word_buffer = []
  for word in words:
    current += len(word) + 1
    if current >= line_length:
      current = len(word)
      lines.append(u' '.join(word_buffer))
      word_buffer = [word]
    else:
      word_buffer.append(word)
  lines.append(u' '.join(word_buffer))

  ret = []
  ret.append(fmt.format(name, lines[0]))
  for line in lines[1:]:
    ret.append(fmt_second.format('', line))

  return u'\n'.join(ret)


class ConsoleConfig(object):
  """Class that contains functions to configure console actions."""

  @classmethod
  def GetConfig(cls):
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

  @classmethod
  def SetPrompt(
      cls, hive_path=None, config=None, prepend_string=None):
    """Sets the prompt string on the console.

    Args:
      hive_path: The hive name or path as a string, this is optional name or
                 location of the loaded hive. If not defined the name is derived
                 from a default string.
      config: The IPython configuration object (instance of
              IPython.terminal.embed.InteractiveShellEmbed), this is optional
              and is automatically derived if not used.
      prepend_string: An optional string that can be injected into the prompt
                      just prior to the command count.
    """
    if hive_path is None:
      path_string = u'Unknown hive loaded'
    else:
      path_string = hive_path

    prompt_strings = [
        r'[{color.LightBlue}\T{color.Normal}]',
        r'{color.LightPurple} ',
        path_string,
        r'\n{color.Normal}']
    if prepend_string is not None:
      prompt_strings.append(u'{0:s} '.format(prepend_string))
    prompt_strings.append(r'[{color.Red}\#{color.Normal}] \$ ')

    if config is None:
      ipython_config = cls.GetConfig()
    else:
      ipython_config = config

    try:
      ipython_config.PromptManager.in_template = r''.join(prompt_strings)
    except AttributeError:
      ipython_config.prompt_manager.in_template = r''.join(prompt_strings)


# TODO: move options out of PregHelper and move parts to front end.
class PregHelper(object):
  """Class that defines various helper functions.

  The purpose of this class is to bridge the plaso generated objects
  with the IPython objects, making it easier to create magic classes
  and provide additional helper functions to the IPython shell.
  """

  def __init__(self, options, preg_tool, hive_storage):
    """Initialize the helper object.

    Args:
      options: A configuration object.
      preg_tool: A preg tool object (instance of PregTool).
      hive_storage: A hive storage object (instance of PregStorage).
    """
    super(PregHelper, self).__init__()
    self._options = options
    self.hive_storage = hive_storage
    self.preg_tool = preg_tool

  def BuildParserMediator(self, event_queue=None):
    """Build the parser object.

    Args:
      event_queue: An event queue object (instance of Queue). This is
                   optional and if a queue is not provided a default
                   one will be provided.

    Returns:
      A parser mediator object (instance of parsers_mediator.ParserMediator).
    """
    if event_queue is None:
      event_queue = single_process.SingleProcessQueue()
    event_queue_producer = queue.ItemQueueProducer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()
    parse_error_queue_producer = queue.ItemQueueProducer(parse_error_queue)

    return parsers_mediator.ParserMediator(
        event_queue_producer, parse_error_queue_producer,
        preg.PregCache.knowledge_base_object)

  def OpenHive(
      self, filename_or_path_spec, hive_collector, hive_collector_name=None,
      codepage='cp1252'):
    """Open a Registry hive based on a collector or a filename.

    Args:
      filename_or_path_spec: file path to the hive as a string or a path spec
                             object (instance of dfvfs.path.path_spec.PathSpec)
      hive_collector: the collector to use (instance of
                      dfvfs.helpers.file_system_searcher.FileSystemSearcher)
      hive_collector_name: optional string denoting the name of the collector
                           used. The default value is None.
      codepage: the default codepage, default is cp1252.

    Returns:
      A hive helper object (instance of PregHiveHelper).
    """
    preg.PregCache.knowledge_base_object.SetDefaultCodepage(codepage)

    if isinstance(filename_or_path_spec, basestring):
      filename = filename_or_path_spec
      path_spec = None
    else:
      filename = filename_or_path_spec.location
      path_spec = filename_or_path_spec

    if not hive_collector:
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_OS, location=filename)
      file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    else:
      file_entry = hive_collector.GetFileEntryByPathSpec(path_spec)

    win_registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    try:
      hive_object = win_registry.OpenFile(
          file_entry, codepage=preg.PregCache.knowledge_base_object.codepage)
    except IOError:
      if filename is not None:
        filename_string = filename
      elif path_spec:
        filename_string = path_spec.location
      else:
        filename_string = u'unknown file path'
      logging.error(
          u'Unable to open Registry hive: {0:s} [{1:s}]'.format(
              filename_string, hive_collector_name))
      return

    return preg.PregHiveHelper(
        hive_object, file_entry=file_entry, collector_name=hive_collector_name)

  def Scan(self, registry_types):
    """Scan for available hives using keyword.

    Args:
      registry_types: A list of keywords to scan for, eg: "NTUSER",
                      "SOFTWARE", etc.
    """
    if not registry_types:
      print(
          u'Unable to scan for an empty keyword. Please specify a keyword, '
          u'eg: NTUSER, SOFTWARE, etc')
      return

    hives, collectors = self.preg_tool.GetHivesAndCollectors(
        registry_types=registry_types)

    if not hives:
      print(u'No new discovered hives.')
      return

    if isinstance(hives, (list, tuple)):
      for hive in hives:
        for name, collector in collectors:
          hive_helper = self.OpenHive(
              hive, hive_collector=collector, hive_collector_name=name)
          if hive_helper:
            self.hive_storage.AppendHive(hive_helper)
    else:
      for name, collector in collectors:
        hive_helper = self.OpenHive(
            hives, hive_collector=collector, hive_collector_name=name)
        if hive_helper:
          self.hive_storage.AppendHive(hive_helper)


class PregTool(storage_media_tool.StorageMediaTool):
  """Class that implements the preg CLI tool."""

  _SOURCE_OPTION = u'image'

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
  RUN_MODE_REG_FILE = 2
  RUN_MODE_REG_PLUGIN = 3
  RUN_MODE_REG_KEY = 4

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: the input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(PregTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._front_end = preg.PregFrontend()
    self._key_path = None
    # TODO: remove after preg options refactor.
    self._options = None
    self._parse_restore_points = False
    self._plugin_names = u''
    self._registry_file = u''
    self._source_path = None
    self._verbose_output = False

    self.list_plugins = False
    self.run_mode = None

  # TODO: refactor to use output_writer.
  def _GetEventBody(self, event_object, file_entry=None, show_hex=False):
    """Returns a list of strings containing information from an event.

    Args:
      event_object: An event object (instance of event.EventObject).
      file_entry: An optional file entry object (instance of dfvfs.FileEntry)
                  that the event originated from. Default is None.
      show_hex: A boolean, if set to True hex dump of the value is included in
                the output. The default value is False.

    Returns:
      A list of strings containing the event body.
    """
    format_string = self._GetFormatString(event_object)

    ret_strings = []

    timestamp_description = getattr(
        event_object, 'timestamp_desc', eventdata.EventTimestamp.WRITTEN_TIME)

    if timestamp_description != eventdata.EventTimestamp.WRITTEN_TIME:
      ret_strings.append(u'<{0:s}>'.format(timestamp_description))

    if hasattr(event_object, 'regvalue'):
      attributes = event_object.regvalue
    else:
      # TODO: Add a function for this to avoid repeating code.
      keys = event_object.GetAttributes().difference(
          event_object.COMPARE_EXCLUDE)
      keys.discard('offset')
      keys.discard('timestamp_desc')
      attributes = {}
      for key in keys:
        attributes[key] = getattr(event_object, key)

    for attribute, value in attributes.items():
      ret_strings.append(format_string.format(attribute, value))

    if show_hex and file_entry:
      event_object.pathspec = file_entry.path_spec
      ret_strings.append(self._FormatHeader(u'Hex Output From Event.', '-'))
      ret_strings.append(
          frontend_utils.OutputWriter.GetEventDataHexDump(event_object))

    return ret_strings

  # TODO: refactor to use output_writer.
  def _GetEventHeader(self, event_object, descriptions, exclude_timestamp):
    """Returns a list of strings that contains a header for the event.

    Args:
      event_object: An event object (instance of event.EventObject).
      descriptions: A list of strings describing the value of the header
                    timestamp.
      exclude_timestamp: A boolean. If it is set to True the method
                         will not include the timestamp in the header.

    Returns:
      A list of strings containing header information for the event.
    """
    format_string = self._GetFormatString(event_object)

    # Create the strings to return.
    ret_strings = []
    ret_strings.append(u'Key information.')
    if not exclude_timestamp:
      for description in descriptions:
        ret_strings.append(format_string.format(
            description, timelib.Timestamp.CopyToIsoFormat(
                event_object.timestamp)))

    if hasattr(event_object, u'keyname'):
      ret_strings.append(
          format_string.format(u'Key Path', event_object.keyname))

    if event_object.timestamp_desc != eventdata.EventTimestamp.WRITTEN_TIME:
      ret_strings.append(format_string.format(
          u'Description', event_object.timestamp_desc))

    ret_strings.append(self._FormatHeader(u'Data', u'-'))

    return ret_strings

  def _GetFormatString(self, event_object):
    """Return back a format string that can be used for a given event object."""
    # Assign a default value to font align length.
    align_length = 15

    # Go through the attributes and see if there is an attribute
    # value that is longer than the default font align length, and adjust
    # it accordingly if found.
    if hasattr(event_object, u'regvalue'):
      attributes = event_object.regvalue.keys()
    else:
      attributes = event_object.GetAttributes().difference(
          event_object.COMPARE_EXCLUDE)

    for attribute in attributes:
      attribute_len = len(attribute)
      if attribute_len > align_length and attribute_len < 30:
        align_length = len(attribute)

    # Create the format string that will be used, using variable length
    # font align length (calculated in the prior step).
    return u'{{0:>{0:d}s}} : {{1!s}}'.format(align_length)

  # TODO: replace by tool.PrintHeader.
  def _FormatHeader(self, header, char='*'):
    """Formats the header as a line of 80 characters with centered text."""
    format_string = '\n{{0:{0:s}^80}}'.format(char)
    return format_string.format(u' {0:s} '.format(header))

  # TODO: Improve check and use dfVFS.
  def _PathExists(self, file_path):
    """Determine if a given file path exists as a file, directory or a device.

    Args:
      file_path: A string denoting the file path that needs checking.

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

  def ListPluginInformation(self):
    """Lists Registry plugin information."""
    plugin_list = self._front_end.GetWindowsRegistryPlugins()

    self.PrintHeader(u'Supported Plugins')
    self.PrintHeader(u'Key Plugins')
    for plugin_class in plugin_list.GetAllKeyPlugins():
      self.PrintColumnValue(plugin_class.NAME, plugin_class.DESCRIPTION)

    self.PrintHeader(u'Value Plugins')
    for plugin_class in plugin_list.GetAllValuePlugins():
      self.PrintColumnValue(plugin_class.NAME, plugin_class.DESCRIPTION)

    self._output_writer.Write(u'\n')

  # TODO: refactor move non tool code into frontend.
  def GetHivesAndCollectors(
      self, registry_types=None, plugin_names=None):
    """Returns a list of discovered Registry hives and collectors.

    Args:
      registry_types: an optional list of Registry types, eg: NTUSER, SAM, etc
                      that should be included. Defaults to None.
      plugin_names: an optional list of strings containing the name of the
                    plugin(s) or an empty string for all the types. Defaults to
                    None.

    Returns:
      A tuple of hives and searchers, where hives is a list that contains
      either a string (location of a Registry hive) or path specs (instance of
      dfvfs.path.path_spec.PathSpec). The searchers is a list of tuples that
      contain the name of the searcher and a searcher object (instance of
      dfvfs.helpers.file_system_searcher.FileSystemSearcher) or None (if no
      searcher is required).

    Raises:
      ValueError: If neither registry_types nor plugin name is passed
                  as a parameter.
      BadConfigOption: If the source scanner is unable to complete due to
                       a source scanner error or back end error in dfvfs.
    """
    if registry_types is None and plugin_names is None:
      raise ValueError(
          u'Missing Registry_types or plugin_name value.')

    if plugin_names is None:
      plugin_names = []
    else:
      plugin_names = [plugin_name.lower() for plugin_name in plugin_names]

    # TODO: use non-preprocess collector with filter to collect hives.

    # TODO: rewrite to always use collector or equiv.
    if not self._source_path:
      searchers = [(u'', None)]
      return registry_types, searchers

    try:
      self.ScanSource(self._front_end)
    except errors.SourceScannerError as exception:
      raise errors.BadConfigOption((
          u'Unable to scan for a supported file system with error: {0:s}\n'
          u'Most likely the image format is not supported by the '
          u'tool.').format(exception))

    searchers = self._GetSearchersForImage(self.GetSourcePathSpec().parent)
    _, searcher = searchers[0]

    # Run preprocessing on image.
    platform = preprocess_interface.GuessOS(searcher)

    preprocess_manager.PreprocessPluginsManager.RunPlugins(
        platform, searcher, preg.PregCache.knowledge_base_object)

    # Create the keyword list if plugins are used.
    plugins_list = self.GetWindowsRegistryPlugins()
    if plugin_names:
      if registry_types is None:
        registry_types = []
      for plugin_name in plugin_names:
        for plugin_class in plugins_list.GetAllKeyPlugins():
          if plugin_name == plugin_class.NAME.lower():
            # If a plugin is available for every Registry type
            # we need to make sure all Registry hives are included.
            if plugin_class.REG_TYPE == u'any':
              for available_type in preg.PregHiveHelper.REG_TYPES.iterkeys():
                if available_type is u'Unknown':
                  continue

                if available_type not in registry_types:
                  registry_types.append(available_type)

            if plugin_class.REG_TYPE not in registry_types:
              registry_types.append(plugin_class.REG_TYPE)

    # Find all the Registry paths we need to check.
    paths = []
    if registry_types:
      for registry_type in registry_types:
        paths.extend(self.GetRegistryFilePaths(
            registry_type=registry_type.upper()))
    else:
      for plugin_name in plugin_names:
        paths.extend(self.GetRegistryFilePaths(plugin_name=plugin_name))

    hives = []
    for path in paths:
      hives.extend(self._FindRegistryPaths(searcher, path))

    return hives, searchers

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
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      logging.error(u'{0:s}'.format(exception))

      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())

      return False

    return True

  # TODO: refactor move non tool code into frontend.
  def ParseHive(
      self, hive_path_or_path_spec, hive_collectors, shell_helper,
      key_paths=None, use_plugins=None, verbose=False):
    """Opens a hive file, and returns information about parsed keys.

    This function takes a path to a hive and a list of collectors (or
    none if the Registry file is passed to the tool).

    The function then opens up the hive inside each collector and runs
    the plugins defined (or all if no plugins are defined) against all
    the keys supplied to it.

    Args:
      hive_path: Full path to the hive file in question.
      hive_collectors: A list of collectors to use (instance of
                       dfvfs.helpers.file_system_searcher.FileSystemSearcher)
      shell_helper: A helper object (instance of PregHelper).
      key_paths: A list of Registry keys paths that are to be parsed.
      use_plugins: A list of plugins used to parse the key, None if all
      plugins should be used.
      verbose: Print more verbose content, like hex dump of extracted events.

    Returns:
      A string containing extracted information.
    """
    if isinstance(hive_path_or_path_spec, basestring):
      hive_path_spec = None
      hive_path = hive_path_or_path_spec
    else:
      hive_path_spec = hive_path_or_path_spec
      hive_path = hive_path_spec.location

    if key_paths is None:
      key_paths = []

    print_strings = []
    for name, hive_collector in hive_collectors:
      # Printing '*' 80 times.
      print_strings.append(u'*' * 80)
      print_strings.append(
          u'{0:>15} : {1:s}{2:s}'.format(u'Hive File', hive_path, name))
      if hive_path_spec:
        current_hive = shell_helper.OpenHive(hive_path_spec, hive_collector)
      else:
        current_hive = shell_helper.OpenHive(hive_path, hive_collector)

      if not current_hive:
        continue

      for key_path in key_paths:
        key_texts = []
        key_dict = {}
        if current_hive.reg_cache:
          key_dict.update(current_hive.reg_cache.attributes.items())

        # TODO: refactor to use a method.
        if preg.PregCache.knowledge_base_object.pre_obj:
          key_dict.update(
              preg.PregCache.knowledge_base_object.pre_obj.__dict__.items())

        key = current_hive.GetKeyByPath(key_path)
        key_texts.append(u'{0:>15} : {1:s}'.format(u'Key Name', key_path))
        if not key:
          key_texts.append(u'Unable to open key: {0:s}'.format(key_path))
          if verbose:
            print_strings.extend(key_texts)
          continue
        key_texts.append(
            u'{0:>15} : {1:d}'.format(u'Subkeys', key.number_of_subkeys))
        key_texts.append(u'{0:>15} : {1:d}'.format(
            u'Values', key.number_of_values))
        key_texts.append(u'')

        if verbose:
          key_texts.append(u'{0:-^80}'.format(u' SubKeys '))
          for subkey in key.GetSubkeys():
            key_texts.append(
                u'{0:>15} : {1:s}'.format(u'Key Name', subkey.path))

        key_texts.append(u'')
        key_texts.append(u'{0:-^80}'.format(u' Plugins '))

        output_string = self.ParseKey(
            key=key, shell_helper=shell_helper, verbose=verbose,
            use_plugins=use_plugins, hive_helper=current_hive)
        key_texts.extend(output_string)

        print_strings.extend(key_texts)

    return u'\n'.join(print_strings)

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self.list_plugins = getattr(options, u'show_info', False)

    if self.list_plugins:
      return

    image = getattr(options, u'image', None)
    if image:
      # TODO: refactor.
      super(PregTool, self).ParseOptions(options)
    else:
      self._ParseInformationalOptions(options)

    registry_file = getattr(options, u'registry_file', None)

    if not image and not registry_file:
      raise errors.BadConfigOption(u'Not enough parameters to proceed.')

    if image:
      self._source_path = image

    if registry_file:
      if not image and not os.path.isfile(registry_file):
        raise errors.BadConfigOption(
            u'Registry file: {0:s} does not exist.'.format(registry_file))

    self._key_path = getattr(options, u'key', None)
    self._parse_restore_points = getattr(options, u'restore_points', False)

    self._verbose_output = getattr(options, u'verbose', False)

    if image:
      file_to_check = image
    else:
      file_to_check = registry_file

    is_file, reason = self._PathExists(file_to_check)
    if not is_file:
      raise errors.BadConfigOption(
          u'Unable to read the input file with error: {0:s}'.format(reason))

    self._plugin_names = getattr(options, u'plugin_names', u'')

    if getattr(options, u'console', False):
      self.run_mode = self.RUN_MODE_CONSOLE
    elif getattr(options, u'key', u'') and registry_file:
      self.run_mode = self.RUN_MODE_REG_KEY
    elif self._plugin_names:
      self.run_mode = self.RUN_MODE_REG_PLUGIN
    elif registry_file:
      self.run_mode = self.RUN_MODE_REG_PLUGIN
    else:
      raise errors.BadConfigOption(
          u'Incorrect usage. You\'ll need to define the path of either '
          u'a storage media image or a Windows Registry file.')

    self._registry_file = registry_file

    # TODO: refactor this.
    self._options = options

  # TODO: refactor move non tool code into frontend.
  def ParseKey(
      self, key, shell_helper, hive_helper, verbose=False, use_plugins=None):
    """Parse a single Registry key and return parsed information.

    Parses the Registry key either using the supplied plugin or trying against
    all available plugins.

    Args:
      key: The Registry key to parse, WinRegKey object or a string.
      shell_helper: A shell helper object (instance of PregHelper).
      hive_helper: A hive object (instance of PregHiveHelper).
      verbose: Print additional information, such as a hex dump.
      use_plugins: A list of plugin names to use, or none if all should be used.

    Returns:
      A list of strings.
    """
    print_strings = []
    if not hive_helper:
      return

    if isinstance(key, basestring):
      key = hive_helper.GetKeyByPath(key)

    if not key:
      return

    # Detect Registry type.
    registry_type = hive_helper.type

    plugins = {}
    plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()

    # Compile a list of plugins we are about to use.
    for weight in plugins_list.GetWeights():
      plugin_list = plugins_list.GetWeightPlugins(weight, registry_type)
      plugins[weight] = []
      for plugin in plugin_list:
        if use_plugins:
          plugin_obj = plugin(reg_cache=hive_helper.reg_cache)
          if plugin_obj.NAME in use_plugins:
            plugins[weight].append(plugin_obj)
        else:
          plugins[weight].append(plugin(
              reg_cache=hive_helper.reg_cache))

    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = preg.PregItemQueueConsumer(event_queue)

    # Build a parser mediator.
    parser_mediator = shell_helper.BuildParserMediator(event_queue)
    parser_mediator.SetFileEntry(hive_helper.file_entry)

    # Run all the plugins in the correct order of weight.
    for weight in plugins:
      for plugin in plugins[weight]:
        plugin.Process(parser_mediator, key=key)
        event_queue_consumer.ConsumeItems()
        if not event_queue_consumer.event_objects:
          continue

        print_strings.append(u'')
        print_strings.append(
            u'{0:^80}'.format(u' ** Plugin : {0:s} **'.format(
                plugin.plugin_name)))
        print_strings.append(u'')
        print_strings.append(u'[{0:s}] {1:s}'.format(
            plugin.REG_TYPE, plugin.DESCRIPTION))
        print_strings.append(u'')
        if plugin.URLS:
          print_strings.append(u'Additional information can be found here:')

          for url in plugin.URLS:
            print_strings.append(u'{0:>17s} {1:s}'.format(u'URL :', url))
          print_strings.append(u'')

        # TODO: move into the event queue consumer.
        event_objects_and_timestamps = {}
        event_object = event_queue_consumer.event_objects.pop(0)
        while event_object:
          preg.PregCache.events_from_last_parse.append(event_object)
          event_objects_and_timestamps.setdefault(
              event_object.timestamp, []).append(event_object)

          if event_queue_consumer.event_objects:
            event_object = event_queue_consumer.event_objects.pop(0)
          else:
            event_object = None

        if not event_objects_and_timestamps:
          continue

        # If there is only a single timestamp then we'll include it in the
        # header, otherwise each event will have it's own timestamp.
        if len(event_objects_and_timestamps) > 1:
          exclude_timestamp_in_header = True
        else:
          exclude_timestamp_in_header = False

        first = True
        for event_timestamp in sorted(event_objects_and_timestamps):
          if first:
            first_event = event_objects_and_timestamps[event_timestamp][0]
            descriptions = set()
            for event_object in event_objects_and_timestamps[event_timestamp]:
              descriptions.add(getattr(event_object, 'timestamp_desc', u''))
            print_strings.extend(self._GetEventHeader(
                first_event, list(descriptions), exclude_timestamp_in_header))
            first = False

          if exclude_timestamp_in_header:
            print_strings.append(u'')
            print_strings.append(u'[{0:s}]'.format(
                timelib.Timestamp.CopyToIsoFormat(event_timestamp)))

          for event_object in event_objects_and_timestamps[event_timestamp]:
            print_strings.append(u'')
            print_strings.extend(self._GetEventBody(
                event_object, hive_helper.file_entry, verbose))

        print_strings.append(u'')

    # Printing '*' 80 times.
    print_strings.append(u'*'*80)
    print_strings.append(u'')

    return print_strings

  def RunModeRegistryFile(self):
    """Run against a Registry file.

    Finds and opens all Registry hives as configured in the configuration
    object and determines the type of Registry file opened. Then it will
    load up all the Registry plugins suitable for that particular Registry
    file, find all Registry keys they are able to parse and run through
    them, one by one.
    """
    # Get all the hives and collectors.
    hives, hive_collectors = self.GetHivesAndCollectors(
        registry_types=[self._registry_file])

    hive_storage = preg.PregStorage()
    shell_helper = PregHelper(self._options, self, hive_storage)
    parser_mediator = shell_helper.BuildParserMediator()

    for hive in hives:
      for collector_name, hive_collector in hive_collectors:
        hive_helper = shell_helper.OpenHive(
            hive, hive_collector=hive_collector,
            hive_collector_name=collector_name)
        hive_type = hive_helper.type

        key_paths = self._front_end.GetRegistryKeysFromHive(
            hive_helper, parser_mediator)
        self._front_end.ExpandKeysRedirect(key_paths)

        plugins_to_run = self._front_end.GetRegistryPluginsFromRegistryType(
            hive_type)
        output_string = self.ParseHive(
            hive, hive_collectors, shell_helper, key_paths=key_paths,
            use_plugins=plugins_to_run, verbose=self._verbose_output)
        self._output_writer.Write(output_string)

  def RunModeRegistryKey(self):
    """Run against a specific Registry key.

    Finds and opens all Registry hives as configured in the configuration
    object and tries to open the Registry key that is stored in the
    configuration object for every detected hive file and parses it using
    all available plugins.
    """
    hives, hive_collectors = self.GetHivesAndCollectors(
        registry_types=[self._registry_file],
        plugin_names=self._plugin_names)

    key_paths = [self._key_path]

    # Expand the keys paths if there is a need (due to Windows redirect).
    self._front_end.ExpandKeysRedirect(key_paths)

    hive_storage = preg.PregStorage()
    shell_helper = PregHelper(self._options, self, hive_storage)

    if hives is None:
      hives = [self._registry_file]

    for hive in hives:
      output_string = self.ParseHive(
          hive, hive_collectors, shell_helper,
          key_paths=key_paths, verbose=self._verbose_output)
      self._output_writer.Write(output_string)

  def RunModeRegistryPlugin(self):
    """Run against a set of Registry plugins."""
    # TODO: Add support for splitting the output to separate files based on
    # each plugin name.
    hives, hive_collectors = self.GetHivesAndCollectors(
        plugin_names=self._plugin_names)

    if hives is None:
      hives = [self._registry_file]

    plugin_list = []
    for plugin_name in self._plugin_names:
      plugin_list.extend(self._front_end.GetRegistryPlugins(plugin_name))

    # In order to get all the Registry keys we need to expand
    # them, but to do so we need to open up one hive so that we
    # create the reg_cache object, which is necessary to fully
    # expand all keys.
    _, hive_collector = hive_collectors[0]
    hive_storage = preg.PregStorage()
    shell_helper = PregHelper(self._options, self, hive_storage)
    hive_helper = shell_helper.OpenHive(hives[0], hive_collector)
    parser_mediator = shell_helper.BuildParserMediator()

    plugins = self._front_end.GetWindowsRegistryPlugins()

    # Get all the appropriate keys from these plugins.
    key_paths = plugins.GetExpandedKeyPaths(
        parser_mediator, reg_cache=hive_helper.reg_cache,
        plugin_names=plugin_list)

    for hive in hives:
      output_string = self.ParseHive(
          hive, hive_collectors, shell_helper,
          key_paths=key_paths, use_plugins=plugin_list,
          verbose=self._verbose_output)
      self._output_writer.Write(output_string)


@magic.magics_class
class PregMagics(magic.Magics):
  """Class that implements the iPython console magic functions."""

  EXPANSION_KEY_OPEN = r'{'
  EXPANSION_KEY_CLOSE = r'}'

  # Match against one instance, not two of the expansion key.
  EXPANSION_RE = re.compile(r'{0:s}{{1}}[^{1:s}]+?{1:s}'.format(
      EXPANSION_KEY_OPEN, EXPANSION_KEY_CLOSE))

  output_writer = sys.stdout

  @magic.line_magic(u'cd')
  def ChangeDirectory(self, key):
    """Change between Registry keys, like a directory tree.

    The key path can either be an absolute path or a relative one.
    Absolute paths can use '.' and '..' to denote current and parent
    directory/key path.

    Args:
      key: The path to the key to traverse to.
    """
    registry_key = None
    key_path = key

    if not key:
      self.ChangeDirectory(u'\\')

    loaded_hive = preg.PregCache.hive_storage.loaded_hive

    if not loaded_hive:
      return

    # Check if we need to expand environment attributes.
    match = self.EXPANSION_RE.search(key)
    if match and u'{0:s}{0:s}'.format(
        self.EXPANSION_KEY_OPEN) not in match.group(0):
      try:
        key = loaded_hive.path_expander.ExpandPath(
            key, pre_obj=preg.PregCache.knowledge_base_object.pre_obj)
      except (KeyError, IndexError):
        pass

    if key.startswith(u'\\'):
      registry_key = loaded_hive.GetKeyByPath(key)
    elif key == '.':
      return
    elif key.startswith(u'.\\'):
      current_path = loaded_hive.GetCurrentRegistryPath()
      _, _, key_path = key.partition(u'\\')
      registry_key = loaded_hive.GetKeyByPath(u'{0:s}\\{1:s}'.format(
          current_path, key_path))
    elif key.startswith(u'..'):
      parent_path, _, _ = loaded_hive.GetCurrentRegistryPath().rpartition(u'\\')
      # We know the path starts with a "..".
      if len(key) == 2:
        key_path = u''
      else:
        key_path = key[3:]
      if parent_path:
        if key_path:
          path = u'{0:s}\\{1:s}'.format(parent_path, key_path)
        else:
          path = parent_path
        registry_key = loaded_hive.GetKeyByPath(path)
      else:
        registry_key = loaded_hive.GetKeyByPath(u'\\{0:s}'.format(key_path))

    else:
      # Check if key is not set at all, then assume traversal from root.
      if not loaded_hive.GetCurrentRegistryPath():
        _ = loaded_hive.GetKeyByPath(u'\\')

      current_key = loaded_hive.GetCurrentRegistryKey()
      if current_key.name == loaded_hive.root_key.name:
        key_path = u'\\{0:s}'.format(key)
      else:
        key_path = u'{0:s}\\{1:s}'.format(current_key.path, key)
      registry_key = loaded_hive.GetKeyByPath(key_path)

    if registry_key:
      if key_path == u'\\':
        path = u'\\'
      else:
        path = registry_key.path

      sanitized_path = path.replace(u'}', u'}}').replace(u'{', u'{{')
      sanitized_path = sanitized_path.replace(u'\\', u'\\\\')
      ConsoleConfig.SetPrompt(
          hive_path=loaded_hive.path, prepend_string=sanitized_path)
    else:
      print(u'Unable to change to: {0:s}'.format(key_path))

  @magic.line_magic('hive')
  def HiveActions(self, line):
    """Define the hive command on the console prompt."""
    if line.startswith('list'):
      print(preg.PregCache.hive_storage.ListHives())

      print(u'')
      print(u'To open a hive, use: hive_open INDEX')
    elif line.startswith('open ') or line.startswith('load '):
      preg.PregCache.hive_storage.SetOpenHive(line[5:])
      hive_helper = preg.PregCache.hive_storage.loaded_hive
      print(u'Opening hive: {0:s} [{1:s}]'.format(
          hive_helper.path, hive_helper.collector_name))
      ConsoleConfig.SetPrompt(hive_path=hive_helper.path)
    elif line.startswith('scan'):
      items = line.split()
      if len(items) < 2:
        print(
            u'Unable to scan for an empty keyword. Please specify a keyword, '
            u'eg: NTUSER, SOFTWARE, etc')
        return

      preg.PregCache.hive_storage.Scan(items[1:])

  @magic.line_magic('ls')
  def ListDirectoryContent(self, line):
    """List all subkeys and values of the current key."""
    if not IsLoaded():
      return

    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False

    sub = []
    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    current_key = current_hive.GetCurrentRegistryKey()
    for key in current_key.GetSubkeys():
      # TODO: move this construction into a separate function in OutputWriter.
      timestamp, _, _ = frontend_utils.OutputWriter.GetDateTimeString(
          key.last_written_timestamp).partition('.')

      sub.append((u'{0:>19s} {1:>15s}  {2:s}'.format(
          timestamp.replace('T', ' '), '[KEY]',
          key.name), True))

    for value in current_key.GetValues():
      if not verbose:
        sub.append((u'{0:>19s} {1:>14s}]  {2:s}'.format(
            u'', '[' + value.data_type_string, value.name), False))
      else:
        if value.DataIsString():
          value_string = u'{0:s}'.format(value.data)
        elif value.DataIsInteger():
          value_string = u'{0:d}'.format(value.data)
        elif value.DataIsMultiString():
          value_string = u'{0:s}'.format(u''.join(value.data))
        elif value.DataIsBinaryData():
          hex_string = binascii.hexlify(value.data)
          # We'll just print the first few bytes, but we need to pad them
          # to make it fit in a single line if shorter.
          leftovers = len(hex_string) % 32
          if leftovers:
            pad = u' ' * (32 - leftovers)
            hex_string += pad

          value_string = frontend_utils.OutputWriter.GetHexDumpLine(
              hex_string, 0)
        else:
          value_string = u''

        sub.append((
            u'{0:>19s} {1:>14s}]  {2:<25s}  {3:s}'.format(
                u'', u'[' + value.data_type_string, value.name, value_string),
            False))

    for entry, subkey in sorted(sub):
      if subkey:
        self.output_writer.write(u'dr-xr-xr-x {0:s}\n'.format(entry))
      else:
        self.output_writer.write(u'-r-xr-xr-x {0:s}\n'.format(entry))

  @magic.line_magic('parse')
  def ParseCurrentKey(self, line):
    """Parse the current key."""
    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False

    if not IsLoaded():
      return

    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    # Clear the last results from parse key.
    preg.PregCache.events_from_last_parse = []

    print_strings = preg.PregCache.shell_helper.preg_tool.ParseKey(
        key=current_hive.GetCurrentRegistryKey(), hive_helper=current_hive,
        shell_helper=preg.PregCache.shell_helper, verbose=verbose)
    self.output_writer.write(u'\n'.join(print_strings))

    # Print out a hex dump of all binary values.
    if verbose:
      header_shown = False
      for value in current_hive.GetCurrentRegistryKey().GetValues():
        if value.DataIsBinaryData():
          if not header_shown:
            header_shown = True
            print(FormatHeader('Hex Dump'))
          # Print '-' 80 times.
          self.output_writer.write(u'-'*80)
          self.output_writer.write(u'\n')
          self.output_writer.write(
              FormatOutputString('Attribute', value.name))
          self.output_writer.write(u'-'*80)
          self.output_writer.write(u'\n')
          self.output_writer.write(
              frontend_utils.OutputWriter.GetHexDump(value.data))
          self.output_writer.write(u'\n')
          self.output_writer.write(u'+-'*40)
          self.output_writer.write(u'\n')

    self.output_writer.flush()

  @magic.line_magic('plugin')
  def ParseWithPlugin(self, line):
    """Parse a Registry key using a specific plugin."""
    if not IsLoaded():
      print(u'No hive loaded, unable to parse.')
      return

    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    if not line:
      print(u'No plugin name added.')
      return

    plugin_name = line
    if '-h' in line:
      items = line.split()
      if len(items) != 2:
        print(u'Wrong usage: plugin [-h] PluginName')
        return
      if items[0] == '-h':
        plugin_name = items[1]
      else:
        plugin_name = items[0]

    hive_type = current_hive.type
    plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()
    plugin_found = False
    for plugin_cls in plugins_list.GetKeyPlugins(hive_type):
      plugin = plugin_cls(reg_cache=current_hive.reg_cache)
      if plugin.plugin_name == plugin_name:
        # If we found the correct plugin.
        plugin_found = True
        break

    if not plugin_found:
      print(u'No plugin named: {0:s} available for Registry type {1:s}'.format(
          plugin_name, hive_type))
      return

    if not hasattr(plugin, 'REG_KEYS'):
      print(u'Plugin: {0:s} has no key information.'.format(line))
      return

    if '-h' in line:
      print(FormatHeader(plugin_name))
      print(FormatOutputString('Description', plugin.__doc__))
      print(u'')
      for registry_key in plugin.expanded_keys:
        print(FormatOutputString('Registry Key', registry_key))
      return

    if not plugin.expanded_keys:
      plugin.ExpandKeys(preg.PregCache.parser_mediator)

    # Clear the last results from parse key.
    preg.PregCache.events_from_last_parse = []

    # Defining outside of for loop for optimization.
    get_key_by_path = current_hive.GetKeyByPath
    for registry_key in plugin.expanded_keys:
      key = get_key_by_path(registry_key)
      if not key:
        print(u'Key: {0:s} not found'.format(registry_key))
        continue

      # Move the current location to the key to be parsed.
      self.ChangeDirectory(registry_key)
      # Parse the key.
      print_strings = preg.PregCache.shell_helper.preg_tool.ParseKey(
          key=current_hive.GetCurrentRegistryKey(), hive_helper=current_hive,
          shell_helper=preg.PregCache.shell_helper, verbose=False,
          use_plugins=[plugin_name])
      self.output_writer.write(u'\n'.join(print_strings))
    self.output_writer.flush()

  @magic.line_magic('pwd')
  def PrintCurrentWorkingDirectory(self, unused_line):
    """Print the current path."""
    if not IsLoaded():
      return

    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    self.output_writer.write(u'{0:s}\n'.format(
        current_hive.GetCurrentRegistryPath()))

  @magic.line_magic('redirect_output')
  def RedirectOutput(self, output_object):
    """Change the output writer to redirect plugin output to a file."""

    if isinstance(output_object, basestring):
      output_object = open(output_object, 'wb')

    if hasattr(output_object, 'write'):
      self.output_writer = output_object


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

  def __init__(self, preg_tool):
    """Initialize the console object.

    Args:
      preg_tool: A preg tool object (instance of PregTool).
    """
    super(PregConsole, self).__init__()
    self._preg_cache = preg.PregCache
    self._preg_tool = preg_tool

  def _CommandGetCurrentKey(self):
    """Command function to retrieve the currently loaded Registry key.

    Returns:
      The currently loaded Registry key (instance of WinPyregfKey) or None
      if there is no loaded key.
    """
    hive_helper = self._preg_cache.GetLoadedHive()
    return hive_helper.GetCurrentRegistryKey()

  def _CommandGetValue(self, value_name):
    """Return a value object from the currently loaded Registry key.

    Args:
      value_name: A string containing the name of the value to be retrieved.

    Returns:
      The Registry value (instance of WinPyregfValue) if it exists, None if
      either there is no currently loaded Registry key or if the value does
      not exist.
    """
    hive_helper = self._preg_cache.GetLoadedHive()

    current_key = hive_helper.GetCurrentRegistryKey()
    if not current_key:
      return

    return current_key.GetValue(value_name)

  def _CommandGetValueData(self, value_name):
    """Return the value data from a value in the currently loaded Registry key.

    Args:
      value_name: A string containing the name of the value to be retrieved.

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
    """Return the total number of Registy hives that are loaded."""
    return len(self._preg_cache.hive_storage)

  def _FormatBanner(self):
    """Formats the banner."""
    header = FormatHeader(
        u'Welcome to PREG - home of the Plaso Windows Registry Parsing.')

    lines_of_text = [
        header,
        u'',
        u'Some of the commands that are available for use are:',
        u'']

    for function_name, description in self._BASE_FUNCTIONS:
      text = self._FormatColumnValue(
          function_name, description, column_width=23)
      lines_of_text.append(text)

    lines_of_text.append(u'')

    if len(self._preg_cache.hive_storage) == 1:
      self._preg_cache.hive_storage.SetOpenHive(0)
      hive_helper = self._preg_cache.GetLoadedHive()
      lines_of_text.append(
          u'Opening hive: {0:s} [{1:s}]'.format(
              hive_helper.path, hive_helper.collector_name))
      ConsoleConfig.SetPrompt(hive_path=hive_helper.path)

    hive_helper = self._preg_cache.GetLoadedHive()
    if hive_helper and hive_helper.name != u'N/A':
      text = u'Registry hive: {0:s} is available and loaded.'.format(
          hive_helper.name)
      lines_of_text.append(text)

    else:
      # TODO: refactor ListHives or PrintHives or equiv. since its a CLI
      # only use case.
      hives = self._preg_cache.hive_storage.ListHives()

      lines_of_text.extend([
          u'More than one Registry file ready for use.',
          u'',
          hives,
          u'',
          (u'Use "hive open INDEX" to load a hive and "hive list" to see a '
           u'list of available hives.')])

    lines_of_text.extend([
        u'',
        u'Happy command line console fu-ing.'])

    return u'\n'.join(lines_of_text)

  def _FormatColumnValue(self, name, description, column_width=25):
    """Formats a value with a name and description aligned to the column width.

    Args:
      name: the name.
      description: the description.
      column_width: optional column width. The default is 25.

    Returns:
      A string containing the formatted column value.
    """
    # TODO: Remove the need to directly call the line length.
    # pylint: disable=protected-access
    line_length = self._preg_tool._LINE_LENGTH - column_width - 3

    # The format string of the first line of the column value.
    primary_format_string = u'{{0:>{0:d}s}} : {{1:s}}\n'.format(column_width)

    # The format string of successive lines of the column value.
    secondary_format_string = u'{{0:<{0:d}s}}{{1:s}}\n'.format(
        column_width + 3)

    if len(description) < line_length:
      return primary_format_string.format(name, description)

    # Split the description in words.
    words = description.split()

    current = 0

    lines = []
    word_buffer = []
    for word in words:
      current += len(word) + 1
      if current >= line_length:
        current = len(word)
        lines.append(u' '.join(word_buffer))
        word_buffer = [word]
      else:
        word_buffer.append(word)
    lines.append(u' '.join(word_buffer))

    # Print the column value on multiple lines.
    lines_of_text = [primary_format_string.format(name, lines[0])]
    for line in lines[1:]:
      lines_of_text.append(secondary_format_string.format(u'', line))

    return u'\n'.join(lines_of_text)

  def _FormatHeader(self, text, character=u'*'):
    """Formats the header as a line with centered text.

    Args:
      text: The header text.
      character: Optional header line character. The default is '*'.

    Returns:
      A string containing the formatted header.
    """
    # TODO: Remove the need to directly call the line length.
    # pylint: disable=protected-access
    format_string = u'{{0:{0:s}^{1:d}}}\n'.format(
        character, self._preg_tool._LINE_LENGTH)
    return format_string.format(u' {0:s} '.format(text))

  def Run(self):
    """Runs the interactive console."""
    hive_storage = preg.PregStorage()
    # TODO: move options out of PregHelper and fix this hack.
    # pylint: disable=protected-access
    shell_helper = PregHelper(
        self._preg_tool._options, self._preg_tool, hive_storage)
    parser_mediator = shell_helper.BuildParserMediator()

    self._preg_cache.parser_mediator = parser_mediator
    self._preg_cache.shell_helper = shell_helper
    self._preg_cache.hive_storage = hive_storage

    # TODO: Remove the need to call the options object.
    # pylint:disable=protected-access
    registry_types = getattr(self._preg_tool._options, u'registry_file', None)
    if isinstance(registry_types, basestring):
      registry_types = registry_types.split(u',')

    if not registry_types:
      registry_types = [
          u'NTUSER', u'USRCLASS', u'SOFTWARE', u'SYSTEM', u'SAM', u'SECURITY']
    self._preg_cache.shell_helper.Scan(registry_types)

    banner = self._FormatBanner()

    # Adding variables in scope.
    namespace = {}

    namespace.update(globals())
    namespace.update({
        u'get_current_key': self._CommandGetCurrentKey,
        u'get_key': self._CommandGetCurrentKey,
        u'get_value': self. _CommandGetValue,
        u'get_value_data': self. _CommandGetValueData,
        u'number_of_hives': self._CommandGetTotalNumberOfLoadedHives,
        u'range_of_hives': self._CommandGetRangeForAllLoadedHives,
        u'options': self._preg_tool._options})

    ipshell_config = ConsoleConfig.GetConfig()

    hive_helper = self._preg_cache.GetLoadedHive()
    if hive_helper:
      hive_path = hive_helper.name
    else:
      hive_path = u'NO HIVE LOADED'

    ConsoleConfig.SetPrompt(hive_path=hive_path, config=ipshell_config)

    # Starting the shell.
    ipshell = InteractiveShellEmbed(
        user_ns=namespace, config=ipshell_config, banner1=banner, exit_msg=u'')
    ipshell.confirm_exit = False

    # Adding "magic" functions.
    ipshell.register_magics(PregMagics)

    # Set autocall to two, making parenthesis not necessary when calling
    # function names (although they can be used and are necessary sometimes,
    # like in variable assignments, etc).
    ipshell.autocall = 2

    # Registering command completion for the magic commands.
    ipshell.set_hook(
        u'complete_command', CommandCompleterCd, str_key='%cd')
    ipshell.set_hook(
        u'complete_command', CommandCompleterVerbose, str_key='%ls')
    ipshell.set_hook(
        u'complete_command', CommandCompleterVerbose, str_key='%parse')
    ipshell.set_hook(
        u'complete_command', CommandCompleterPlugins, str_key='%plugin')

    ipshell()


# Completer commands need to be top level methods or directly callable
# and cannot be part of a class that needs to be initialized.
def CommandCompleterCd(unused_console, unused_core_completer):
  """Command completer function for cd."""
  return_list = []
  hive_helper = preg.PregCache.GetLoadedHive()
  current_key = hive_helper.GetCurrentRegistryKey()
  for key in current_key.GetSubkeys():
    return_list.append(key.name)

  return return_list


# Completer commands need to be top level methods or directly callable
# and cannot be part of a class that needs to be initialized.
def CommandCompleterPlugins(unused_console, core_completer):
  """Command completer function for plugins.

  Args:
    core_completer: an IPython completer object (instance of completer.Bunch).
  """
  ret_list = []

  if not IsLoaded():
    return ret_list

  if not u'-h' in core_completer.line:
    ret_list.append(u'-h')

  plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()

  hive_helper = preg.PregCache.GetLoadedHive()
  hive_type = hive_helper.type

  for plugin_cls in plugins_list.GetKeyPlugins(hive_type):
    plugins_list = plugin_cls(reg_cache=hive_helper.reg_cache)

    plugin_name = plugins_list.plugin_name

    if plugin_name == u'winreg_default':
      continue
    ret_list.append(plugin_name)

  return ret_list


# Completer commands need to be top level methods or directly callable
# and cannot be part of a class that needs to be initialized.
def CommandCompleterVerbose(unused_console, core_completer):
  """Command completer function for verbose output.

  Args:
    core_completer: an IPython completer object (instance of completer.Bunch).
  """
  if u'-v' in core_completer.line:
    return []
  else:
    return [u'-v']


def IsLoaded():
  """Checks if a Windows Registry Hive is loaded."""
  hive_helper = preg.PregCache.hive_storage.loaded_hive
  if not hive_helper:
    return False

  current_key = hive_helper.GetCurrentRegistryKey()
  if hasattr(current_key, u'path'):
    return True

  if hive_helper.name != u'N/A':
    return True

  print(
      u'No hive loaded, cannot complete action. Use "hive list" '
      u'and "hive open" to load a hive.')
  return False


def Main():
  """Run the tool."""
  tool = PregTool()

  if not tool.ParseArguments():
    return False

  have_list_option = False
  if tool.list_plugins:
    tool.ListPluginInformation()
    have_list_option = True

  if have_list_option:
    return True

  if tool.run_mode == tool.RUN_MODE_REG_KEY:
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
