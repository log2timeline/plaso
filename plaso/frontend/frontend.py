# -*- coding: utf-8 -*-
"""The common front-end functionality."""

import abc
import locale
import logging
import os
import sys

from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import context
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.lib import errors
from plaso.lib import timelib


# pylint: disable=logging-format-interpolation
class FrontendInputReader(object):
  """Class that implements the input reader interface for the engine."""

  @abc.abstractmethod
  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """


class FrontendOutputWriter(object):
  """Class that implements the output writer interface for the engine."""

  @abc.abstractmethod
  def Write(self, string):
    """Writes a string to the output.

    Args:
      string: A string containing the output.
    """


class StdinFrontendInputReader(object):
  """Class that implements a stdin input reader."""

  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """
    return sys.stdin.readline()


class StdoutFrontendOutputWriter(object):
  """Class that implements a stdout output writer."""

  ENCODING = u'utf-8'

  def Write(self, string):
    """Writes a string to the output.

    Args:
      string: A string containing the output.
    """
    try:
      sys.stdout.write(string.encode(self.ENCODING))
    except UnicodeEncodeError:
      logging.error(
          u'Unable to properly write output, line will be partially '
          u'written out.')
      sys.stdout.write(u'LINE ERROR')
      sys.stdout.write(string.encode(self.ENCODING, 'ignore'))


class Frontend(object):
  """Class that implements a front-end."""

  # The maximum length of the line in number of characters.
  _LINE_LENGTH = 80

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of FrontendInputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of FrontendOutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(Frontend, self).__init__()
    self._input_reader = input_reader
    self._output_writer = output_writer

    # TODO: add preferred_encoding support of the output writer.
    self.preferred_encoding = locale.getpreferredencoding().lower()

  def PrintColumnValue(self, name, description, column_length=25):
    """Prints a value with a name and description aligned to the column length.

    Args:
      name: The name.
      description: The description.
      column_length: Optional column length. The default is 25.
    """
    line_length = self._LINE_LENGTH - column_length - 3

    # The format string of the first line of the column value.
    primary_format_string = u'{{0:>{0:d}s}} : {{1:s}}\n'.format(column_length)

    # The format string of successive lines of the column value.
    secondary_format_string = u'{{0:<{0:d}s}}{{1:s}}\n'.format(
        column_length + 3)

    if len(description) < line_length:
      self._output_writer.Write(primary_format_string.format(name, description))
      return

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
    self._output_writer.Write(primary_format_string.format(name, lines[0]))
    for line in lines[1:]:
      self._output_writer.Write(secondary_format_string.format(u'', line))

  def PrintHeader(self, text, character='*'):
    """Prints the header as a line with centered text.

    Args:
      text: The header text.
      character: Optional header line character. The default is '*'.
    """
    self._output_writer.Write(u'\n')

    format_string = u'{{0:{0:s}^{1:d}}}\n'.format(character, self._LINE_LENGTH)
    header_string = format_string.format(u' {0:s} '.format(text))
    self._output_writer.Write(header_string)

  def PrintSeparatorLine(self):
    """Prints a separator line."""
    self._output_writer.Write(u'{0:s}\n'.format(u'-' * self._LINE_LENGTH))


class StorageMediaFrontend(Frontend):
  """Class that implements a front-end with storage media support."""

  # For context see: http://en.wikipedia.org/wiki/Byte
  _UNITS_1000 = [u'B', u'kB', u'MB', u'GB', u'TB', u'EB', u'ZB', u'YB']
  _UNITS_1024 = [u'B', u'KiB', u'MiB', u'GiB', u'TiB', u'EiB', u'ZiB', u'YiB']

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of FrontendInputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of FrontendOutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(StorageMediaFrontend, self).__init__(input_reader, output_writer)
    self._partition_offset = None
    self._process_vss = True
    self._resolver_context = context.Context()
    self._scan_context = source_scanner.SourceScannerContext()
    self._source_path = None
    self._source_scanner = source_scanner.SourceScanner()
    self._vss_stores = None

  def _GetHumanReadableSize(self, size):
    """Retrieves a human readable string of the size.

    Args:
      size: The size in bytes.

    Returns:
      A human readable string of the size.
    """
    magnitude_1000 = 0
    size_1000 = float(size)
    while size_1000 >= 1000:
      size_1000 /= 1000
      magnitude_1000 += 1

    magnitude_1024 = 0
    size_1024 = float(size)
    while size_1024 >= 1024:
      size_1024 /= 1024
      magnitude_1024 += 1

    size_string_1000 = None
    if magnitude_1000 > 0 and magnitude_1000 <= 7:
      size_string_1000 = u'{0:.1f}{1:s}'.format(
          size_1000, self._UNITS_1000[magnitude_1000])

    size_string_1024 = None
    if magnitude_1024 > 0 and magnitude_1024 <= 7:
      size_string_1024 = u'{0:.1f}{1:s}'.format(
          size_1024, self._UNITS_1024[magnitude_1024])

    if not size_string_1000 or not size_string_1024:
      return u'{0:d} B'.format(size)

    return u'{0:s} / {1:s} ({2:d} B)'.format(
        size_string_1024, size_string_1000, size)

  def _GetPartitionIdentifierFromUser(self, volume_system, volume_identifiers):
    """Asks the user to provide the partitioned volume identifier.

    Args:
      volume_system: The volume system (instance of dfvfs.TSKVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    self._output_writer.Write(
        u'The following partitions were found:\n'
        u'Identifier\tOffset (in bytes)\tSize (in bytes)\n')

    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.FileSystemScannerError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      volume_extent = volume.extents[0]
      self._output_writer.Write(
          u'{0:s}\t\t{1:d} (0x{1:08x})\t{2:s}\n'.format(
              volume.identifier, volume_extent.offset,
              self._GetHumanReadableSize(volume_extent.size)))

    self._output_writer.Write(u'\n')

    while True:
      self._output_writer.Write(
          u'Please specify the identifier of the partition that should '
          u'be processed:\nNote that you can abort with Ctrl^C.\n')

      selected_volume_identifier = self._input_reader.Read()
      selected_volume_identifier = selected_volume_identifier.strip()

      if selected_volume_identifier in volume_identifiers:
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported partition identifier, please try again or abort '
          u'with Ctrl^C.\n'
          u'\n')

    return selected_volume_identifier

  def _GetVolumeTSKPartition(
      self, scan_context, partition_number=None, partition_offset=None):
    """Determines the volume path specification.

    Args:
      scan_context: the scan context (instance of dfvfs.ScanContext).
      partition_number: Optional preferred partition number. The default is
                        None.
      partition_offset: Optional preferred partition byte offset. The default
                        is None.

    Returns:
      The volume scan node (instance of dfvfs.SourceScanNode) or None
      if no supported partition was found.

    Raises:
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan context
                          is invalid.
      RuntimeError: if the volume for a specific identifier cannot be
                    retrieved.
    """
    if (not scan_context or not scan_context.last_scan_node or
        not scan_context.last_scan_node.path_spec):
      raise errors.SourceScannerError(u'Invalid scan context.')

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(scan_context.last_scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      logging.info(u'No supported partitions found.')
      return

    if partition_number is not None and partition_number > 0:
      # Plaso uses partition numbers starting with 1 while dfvfs expects
      # the volume index to start with 0.
      volume = volume_system.GetVolumeByIndex(partition_number - 1)
      if volume:
        volume_location = u'/{0:s}'.format(volume.identifier)
        volume_scan_node = scan_context.last_scan_node.GetSubNodeByLocation(
            volume_location)
        if not volume_scan_node:
          raise RuntimeError(
              u'Unable to retrieve volume scan node by location: {0:s}'.format(
                  volume_location))
        return volume_scan_node

      logging.warning(u'No such partition: {0:d}.'.format(partition_number))

    if partition_offset is not None:
      for volume in volume_system.volumes:
        volume_extent = volume.extents[0]
        if volume_extent.offset == partition_offset:
          volume_location = u'/{0:s}'.format(volume.identifier)
          volume_scan_node = scan_context.last_scan_node.GetSubNodeByLocation(
              volume_location)
          if not volume_scan_node:
            raise RuntimeError((
                u'Unable to retrieve volume scan node by location: '
                u'{0:s}').format(volume_location))
          return volume_scan_node

      logging.warning(
          u'No such partition with offset: {0:d} (0x{0:08x}).'.format(
              partition_offset))

    if len(volume_identifiers) == 1:
      volume_location = u'/{0:s}'.format(volume_identifiers[0])

    else:
      try:
        selected_volume_identifier = self._GetPartitionIdentifierFromUser(
            volume_system, volume_identifiers)
      except KeyboardInterrupt:
        raise errors.UserAbort(u'File system scan aborted.')

      volume = volume_system.GetVolumeByIdentifier(selected_volume_identifier)
      if not volume:
        raise RuntimeError(
            u'Unable to retrieve volume by identifier: {0:s}'.format(
                selected_volume_identifier))

      volume_location = u'/{0:s}'.format(selected_volume_identifier)

    volume_scan_node = scan_context.last_scan_node.GetSubNodeByLocation(
        volume_location)
    if not volume_scan_node:
      raise RuntimeError(
          u'Unable to retrieve volume scan node by location: {0:s}'.format(
              volume_location))
    return volume_scan_node

  def _GetVolumeVssStoreIdentifiers(self, scan_context, vss_stores=None):
    """Determines the VSS store identifiers.

    Args:
      scan_context: the scan context (instance of dfvfs.ScanContext).
      vss_stores: Optional list of preferred VSS stored identifiers. The
                  default is None.

    Raises:
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan context
                          is invalid.
    """
    if (not scan_context or not scan_context.last_scan_node or
        not scan_context.last_scan_node.path_spec):
      raise errors.SourceScannerError(u'Invalid scan context.')

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(scan_context.last_scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      return

    try:
      self._vss_stores = self._GetVssStoreIdentifiersFromUser(
          volume_system, volume_identifiers, vss_stores=vss_stores)
    except KeyboardInterrupt:
      raise errors.UserAbort(u'File system scan aborted.')

    return

  def _GetVssStoreIdentifiersFromUser(
      self, volume_system, volume_identifiers, vss_stores=None):
    """Asks the user to provide the VSS store identifiers.

    Args:
      volume_system: The volume system (instance of dfvfs.VShadowVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.
      vss_stores: Optional list of preferred VSS stored identifiers. The
                  default is None.

    Returns:
      The list of selected VSS store identifiers or None.

    Raises:
      SourceScannerError: if the source cannot be processed.
    """
    normalized_volume_identifiers = []
    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.SourceScannerError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      try:
        volume_identifier = int(volume.identifier[3:], 10)
        normalized_volume_identifiers.append(volume_identifier)
      except ValueError:
        pass

    if vss_stores:
      if len(vss_stores) == 1 and vss_stores[0] == 'all':
        # We need to set the stores to cover all vss stores.
        vss_stores = range(1, volume_system.number_of_volumes + 1)

      if not set(vss_stores).difference(
          normalized_volume_identifiers):
        return vss_stores

    print_header = True
    while True:
      if print_header:
        self._output_writer.Write(
            u'The following Volume Shadow Snapshots (VSS) were found:\n'
            u'Identifier\tVSS store identifier\tCreation Time\n')

        for volume_identifier in volume_identifiers:
          volume = volume_system.GetVolumeByIdentifier(volume_identifier)
          if not volume:
            raise errors.SourceScannerError(
                u'Volume missing for identifier: {0:s}.'.format(
                    volume_identifier))

          vss_identifier = volume.GetAttribute('identifier')
          vss_creation_time = volume.GetAttribute('creation_time')
          vss_creation_time = timelib.Timestamp.FromFiletime(
              vss_creation_time.value)
          vss_creation_time = timelib.Timestamp.CopyToIsoFormat(
              vss_creation_time)
          self._output_writer.Write(u'{0:s}\t\t{1:s}\t{2:s}\n'.format(
              volume.identifier, vss_identifier.value, vss_creation_time))

        self._output_writer.Write(u'\n')

        print_header = False

      self._output_writer.Write(
          u'Please specify the identifier(s) of the VSS that should be '
          u'processed:\nNote that a range of stores can be defined as: 3..5. '
          u'Multiple stores can\nbe defined as: 1,3,5 (a list of comma '
          u'separated values). Ranges and lists can\nalso be combined '
          u'as: 1,3..5. The first store is 1. If no stores are specified\n'
          u'none will be processed. You can abort with Ctrl^C.\n')

      selected_vss_stores = self._input_reader.Read()

      selected_vss_stores = selected_vss_stores.strip()
      if not selected_vss_stores:
        break

      try:
        selected_vss_stores = self._ParseVssStores(selected_vss_stores)
      except errors.BadConfigOption:
        selected_vss_stores = []

      if not set(selected_vss_stores).difference(normalized_volume_identifiers):
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported VSS identifier(s), please try again or abort with '
          u'Ctrl^C.\n'
          u'\n')

    return selected_vss_stores

  def _ParseVssStores(self, vss_stores):
    """Parses the user specified VSS stores stirng.

    Args:
      vss_stores: a string containing the VSS stores.
                  Where 1 represents the first store.

    Returns:
      The list of VSS stores.

    Raises:
      BadConfigOption: if the VSS stores option is invalid.
    """
    if not vss_stores:
      return []

    if vss_stores == u'all':
      # We want to process all the VSS stores.
      return [u'all']

    stores = []
    for vss_store_range in vss_stores.split(u','):
      # Determine if the range is formatted as 1..3 otherwise it indicates
      # a single store number.
      if u'..' in vss_store_range:
        first_store, last_store = vss_store_range.split(u'..')
        try:
          first_store = int(first_store, 10)
          last_store = int(last_store, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid VSS store range: {0:s}.'.format(vss_store_range))

        for store_number in range(first_store, last_store + 1):
          if store_number not in stores:
            stores.append(store_number)
      else:
        try:
          store_number = int(vss_store_range, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid VSS store range: {0:s}.'.format(vss_store_range))

        if store_number not in stores:
          stores.append(store_number)

    return sorted(stores)

  def _ScanSource(
      self, partition_number=None, partition_offset=None, enable_vss=False,
      vss_stores=None):
    """Scans the source path for volume and file systems.

    This functions sets the internal source path specification and source
    type values. The arguments provide the preferred source parameters
    but will be ignored if they are not relevant.

    Args:
      partition_number: optional partition number. The default is None.
      partition_offset: optional partition offset in bytes. The default is None.
      enable_vss: optional boolean value to indicate if VSS should be processed.
                  The default is False.
      vss_stores: optional list of VSS stores. The default is None, which
                  represents all stores if enable_vss is True.

    Raises:
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan context
                          is invalid.
    """
    # Note that os.path.exists() does not support Windows device paths.
    if (not self._source_path.startswith(u'\\\\.\\') and
        not os.path.exists(self._source_path)):
      raise errors.SourceScannerError(
          u'No such device, file or directory: {0:s}.'.format(
              self._source_path))

    # Use the dfVFS source scanner to do the actual scanning.
    scan_path_spec = None

    self._scan_context.OpenSourcePath(self._source_path)

    while True:
      last_scan_node = self._scan_context.last_scan_node
      try:
        self._scan_context = self._source_scanner.Scan(
            self._scan_context, scan_path_spec=scan_path_spec)
      except dfvfs_errors.BackEndError as exception:
        raise errors.SourceScannerError(
            u'Unable to scan source, with error: {0:s}'.format(exception))

      # The source is a directory or file.
      if self._scan_context.source_type in [
          self._scan_context.SOURCE_TYPE_DIRECTORY,
          self._scan_context.SOURCE_TYPE_FILE]:
        break

      if (not self._scan_context.last_scan_node or
          self._scan_context.last_scan_node == last_scan_node):
        raise errors.SourceScannerError(
            u'No supported file system found in source: {0:s}.'.format(
                self._source_path))

      # The source scanner found a file system.
      if self._scan_context.last_scan_node.type_indicator in [
          dfvfs_definitions.TYPE_INDICATOR_TSK]:
        break

      # The source scanner found a BitLocker encrypted volume and we need
      # a credential to unlock the volume.
      if self._scan_context.last_scan_node.type_indicator in [
          dfvfs_definitions.TYPE_INDICATOR_BDE]:
        # TODO: ask for password.
        raise errors.SourceScannerError(
            u'BitLocker encrypted volume not yet supported.')

      # The source scanner found a partition table and we need to determine
      # which partition needs to be processed.
      elif self._scan_context.last_scan_node.type_indicator in [
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION]:
        scan_node = self._GetVolumeTSKPartition(
            self._scan_context, partition_number=partition_number,
            partition_offset=partition_offset)
        if not scan_node:
          break
        self._scan_context.last_scan_node = scan_node

        self._partition_offset = getattr(
            scan_node.path_spec, u'start_offset', 0)

      elif self._scan_context.last_scan_node.type_indicator in [
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW]:
        if enable_vss:
          self._GetVolumeVssStoreIdentifiers(
              self._scan_context, vss_stores=vss_stores)

        # Get the scan node of the current volume.
        scan_node = self._scan_context.last_scan_node.GetSubNodeByLocation(u'/')
        self._scan_context.last_scan_node = scan_node
        break

      else:
        raise errors.SourceScannerError(
            u'Unsupported volume system found in source: {0:s}.'.format(
                self._source_path))

    self._source_type = self._scan_context.source_type

    if self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:

      if self._scan_context.last_scan_node.type_indicator not in [
          dfvfs_definitions.TYPE_INDICATOR_TSK]:
        logging.warning(
            u'Unsupported file system falling back to single file mode.')
        self._source_type = self._scan_context.source_type

      elif self._partition_offset is None:
        self._partition_offset = 0

  def AddImageOptions(self, argument_group):
    """Adds the storage media image options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'-o', u'--offset', dest=u'image_offset', action=u'store', default=None,
        type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of sectors. A sector is 512 bytes in size by default '
            u'this can be overwritten with the --sector_size option.'))

    argument_group.add_argument(
        u'--sector_size', u'--sector-size', dest=u'bytes_per_sector',
        action=u'store', type=int, default=512, help=(
            u'The number of bytes per sector, which is 512 by default.'))

    argument_group.add_argument(
        u'--ob', u'--offset_bytes', u'--offset_bytes',
        dest=u'image_offset_bytes', action=u'store', default=None, type=int,
        help=(
            u'The offset of the volume within the storage media image in '
            u'number of bytes.'))

  def AddVssProcessingOptions(self, argument_group):
    """Adds the VSS processing options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--no_vss', u'--no-vss', dest=u'no_vss', action=u'store_true',
        default=False, help=(
            u'Do not scan for Volume Shadow Snapshots (VSS). This means that '
            u'VSS information will not be included in the extraction phase.'))

    argument_group.add_argument(
        u'--vss_stores', u'--vss-stores', dest=u'vss_stores', action=u'store',
        type=str, default=None, help=(
            u'Define Volume Shadow Snapshots (VSS) (or stores that need to be '
            u'processed. A range of stores can be defined as: \'3..5\'. '
            u'Multiple stores can be defined as: \'1,3,5\' (a list of comma '
            u'separated values). Ranges and lists can also be combined as: '
            u'\'1,3..5\'. The first store is 1.'))

  # TODO: remove this when support to handle multiple partitions is added.
  def GetSourcePathSpec(self):
    """Retrieves the source path specification.

    Returns:
      The source path specification (instance of dfvfs.PathSpec) or None.
    """
    if self._scan_context and self._scan_context.last_scan_node:
      return self._scan_context.last_scan_node.path_spec

  def ParseOptions(self, options, source_option=u'source'):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: optional name of the source option. The default is source.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    if not options:
      raise errors.BadConfigOption(u'Missing options.')

    self._source_path = getattr(options, source_option, None)
    if not self._source_path:
      raise errors.BadConfigOption(u'Missing source path.')

    if isinstance(self._source_path, str):
      encoding = sys.stdin.encoding

      # Note that sys.stdin.encoding can be None.
      if not encoding:
        encoding = self.preferred_encoding

      # Note that the source path option can be an encoded byte string
      # and we need to turn it into an Unicode string.
      try:
        self._source_path = unicode(
            self._source_path.decode(encoding))
      except UnicodeDecodeError as exception:
        raise errors.BadConfigOption((
            u'Unable to convert source path to Unicode with error: '
            u'{0:s}.').format(exception))

    elif not isinstance(self._source_path, unicode):
      raise errors.BadConfigOption(
          u'Unsupported source path, string type required.')

    self._source_path = os.path.abspath(self._source_path)

  def ScanSource(self, options):
    """Scans the source path for volume and file systems.

    This functions sets the internal source path specification and source
    type values.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan context
                          is invalid.
    """
    partition_number = getattr(options, u'partition_number', None)
    if (partition_number is not None and
        isinstance(partition_number, basestring)):
      try:
        partition_number = int(partition_number, 10)
      except ValueError:
        logging.warning(u'Invalid partition number: {0:s}.'.format(
            partition_number))
        partition_number = None

    partition_offset = getattr(options, u'image_offset_bytes', None)
    if (partition_offset is not None and
        isinstance(partition_offset, basestring)):
      try:
        partition_offset = int(partition_offset, 10)
      except ValueError:
        logging.warning(u'Invalid image offset bytes: {0:s}.'.format(
            partition_offset))
        partition_offset = None

    if partition_offset is None and hasattr(options, u'image_offset'):
      image_offset = getattr(options, u'image_offset')
      bytes_per_sector = getattr(options, u'bytes_per_sector', 512)

      if isinstance(image_offset, basestring):
        try:
          image_offset = int(image_offset, 10)
        except ValueError:
          logging.warning(u'Invalid image offset: {0:s}.'.format(image_offset))
          image_offset = None

      if isinstance(bytes_per_sector, basestring):
        try:
          bytes_per_sector = int(bytes_per_sector, 10)
        except ValueError:
          logging.warning(u'Invalid bytes per sector: {0:s}.'.format(
              bytes_per_sector))
          bytes_per_sector = 512

      if image_offset:
        partition_offset = image_offset * bytes_per_sector

    self._process_vss = not getattr(options, u'no_vss', False)
    vss_stores = None
    if self._process_vss:
      vss_stores = getattr(options, u'vss_stores', None)
      if vss_stores:
        vss_stores = self._ParseVssStores(vss_stores)

    return self._ScanSource(
        partition_number=partition_number, partition_offset=partition_offset,
        enable_vss=self._process_vss, vss_stores=vss_stores)


class Options(object):
  """A simple configuration object."""
