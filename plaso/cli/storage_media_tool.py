# -*- coding: utf-8 -*-
"""The storage media CLI tool."""

import logging
import os
import sys

from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import tools
from plaso.lib import errors
from plaso.lib import timelib


class StorageMediaTool(tools.CLITool):
  """Class that implements a storage media CLI tool."""

  _DEFAULT_BYTES_PER_SECTOR = 512
  _SOURCE_OPTION = u'source'

  # For context see: http://en.wikipedia.org/wiki/Byte
  _UNITS_1000 = [u'B', u'kB', u'MB', u'GB', u'TB', u'EB', u'ZB', u'YB']
  _UNITS_1024 = [u'B', u'KiB', u'MiB', u'GiB', u'TiB', u'EiB', u'ZiB', u'YiB']

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
    super(StorageMediaTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._filter_file = None
    # TODO: refactor to partitions.
    self._partition_string = None
    self._partition_offset = None
    self._process_vss = False
    # TODO: refactor to front-end.
    self._source_scanner = source_scanner.SourceScanner()
    self._source_path = None
    self._source_path_specs = []
    self._vss_stores = None

  def _FormatHumanReadableSize(self, size):
    """Formats the size as a human readable string.

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

  # TODO: refactor this method that it become more clear what it is
  # supposed to do.
  def _GetTSKPartitionIdentifiers(
      self, scan_node, partition_string=None, partition_offset=None):
    """Determines the TSK partition identifiers.

    This method first checks for the preferred partition number, then for
    the preferred partition offset and falls back to prompt the user if
    no usable preferences were specified.

    Args:
      scan_node: the scan node (instance of dfvfs.ScanNode).
      partition_string: Optional preferred partition number string. The default
                        is None.
      partition_offset: Optional preferred partition byte offset. The default
                        is None.

    Returns:
      A list of partition identifiers.

    Raises:
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan node is invalid.
      RuntimeError: if the volume for a specific identifier cannot be
                    retrieved.
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

    if partition_string == u'all':
      return volume_identifiers

    if partition_string is not None and not partition_string.startswith(u'p'):
      return volume_identifiers

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
      if volume:
        return [u'p{0:d}'.format(partition_number)]

      logging.warning(u'No such partition: {0:d}.'.format(partition_number))

    if partition_offset is not None:
      for volume in volume_system.volumes:
        volume_extent = volume.extents[0]
        if volume_extent.offset == partition_offset:
          return [volume.identifier]

      logging.warning(
          u'No such partition with offset: {0:d} (0x{0:08x}).'.format(
              partition_offset))

    if len(volume_identifiers) == 1:
      return volume_identifiers

    try:
      selected_volume_identifier = self._PromptUserForPartitionIdentifier(
          volume_system, volume_identifiers)
    except KeyboardInterrupt:
      raise errors.UserAbort(u'File system scan aborted.')

    if selected_volume_identifier == u'all':
      return volume_identifiers

    return [selected_volume_identifier]

  def _GetVSSStoreIdentifiers(self, scan_node, vss_stores=None):
    """Determines the VSS store identifiers.

    Args:
      scan_node: the scan node (instance of dfvfs.ScanNode).
      vss_stores: Optional list of preferred VSS store identifiers. The
                  default is None.

    Returns:
      A list of VSS store identifiers.

    Raises:
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan node is invalid.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError(u'Invalid scan node.')

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    # TODO: refactor to front-end.
    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      return []

    try:
      selected_store_identifiers = self._PromptUserForVSSStoreIdentifiers(
          volume_system, volume_identifiers, vss_stores=vss_stores)
    except KeyboardInterrupt:
      raise errors.UserAbort(u'File system scan aborted.')

    return selected_store_identifiers

  def _ParseFilterOptions(self, options):
    """Parses the filter options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    filter_file = getattr(options, u'file_filter', None)

    if not filter_file:
      return

    if self._data_location:
      filter_file_base = os.path.basename(filter_file)
      filter_file_check = os.path.join(self._data_location, filter_file_base)
      if os.path.isfile(filter_file_check):
        self._filter_file = filter_file_check
        return

    if not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'No such collection filter file: {0:s}.'.format(filter_file))

    self._filter_file = filter_file

  def _ParseStorageMediaImageOptions(self, options):
    """Parses the storage media image options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._partition_string = getattr(options, u'partition_number', None)
    if self._partition_string not in [None, u'all']:
      if not isinstance(self._partition_string, basestring):
        raise errors.BadConfigOption(
            u'Invalid partition number {0!s}.'.format(
                self._partition_string))
      try:
        partition_number = int(self._partition_string, 10)
        self._partition_string = u'p{0:d}'.format(partition_number)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid partition number: {0:s}.'.format(self._partition_string))

    self._partition_offset = getattr(options, u'image_offset_bytes', None)
    if (self._partition_offset is not None and
        isinstance(self._partition_offset, basestring)):
      try:
        self._partition_offset = int(self._partition_offset, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid image offset bytes: {0:s}.'.format(
                self._partition_offset))

    if self._partition_offset is None and hasattr(options, u'image_offset'):
      image_offset = getattr(options, u'image_offset')
      bytes_per_sector = getattr(
          options, u'bytes_per_sector', self._DEFAULT_BYTES_PER_SECTOR)

      if isinstance(image_offset, basestring):
        try:
          image_offset = int(image_offset, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid image offset: {0:s}.'.format(image_offset))

      if isinstance(bytes_per_sector, basestring):
        try:
          bytes_per_sector = int(bytes_per_sector, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid bytes per sector: {0:s}.'.format(bytes_per_sector))

      if image_offset:
        self._partition_offset = image_offset * bytes_per_sector

  def _ParseVSSProcessingOptions(self, options):
    """Parses the VSS processing options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._process_vss = not getattr(options, u'no_vss', False)
    if self._process_vss:
      vss_stores = getattr(options, u'vss_stores', None)
    else:
      vss_stores = None

    if vss_stores:
      vss_stores = self._ParseVSSStoresString(vss_stores)

    self._vss_stores = vss_stores

  def _ParseVSSStoresString(self, vss_stores):
    """Parses the user specified VSS stores string.

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
        if vss_store_range.startswith(u'vss'):
          vss_store_range = vss_store_range[3:]

        try:
          store_number = int(vss_store_range, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid VSS store range: {0:s}.'.format(vss_store_range))

        if store_number not in stores:
          stores.append(store_number)

    return sorted(stores)

  def _PromptUserForPartitionIdentifier(
      self, volume_system, volume_identifiers):
    """Prompts the user to provide a partition identifier.

    Args:
      volume_system: The volume system (instance of dfvfs.TSKVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.

    Returns:
      A string containing the partition identifier or "all".

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    self._output_writer.Write(
        u'The following partitions were found:\n'
        u'Identifier\tOffset (in bytes)\tSize (in bytes)\n')

    for volume_identifier in sorted(volume_identifiers):
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.FileSystemScannerError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      volume_extent = volume.extents[0]
      self._output_writer.Write(
          u'{0:s}\t\t{1:d} (0x{1:08x})\t{2:s}\n'.format(
              volume.identifier, volume_extent.offset,
              self._FormatHumanReadableSize(volume_extent.size)))

    self._output_writer.Write(u'\n')

    while True:
      self._output_writer.Write(
          u'Please specify the identifier of the partition that should be '
          u'processed.\nAll partitions can be defined as: "all". Note that you '
          u'can abort with Ctrl^C.\n')

      selected_volume_identifier = self._input_reader.Read()
      selected_volume_identifier = selected_volume_identifier.strip()

      if not selected_volume_identifier.startswith(u'p'):
        try:
          partition_number = int(selected_volume_identifier, 10)
          selected_volume_identifier = u'p{0:d}'.format(partition_number)
        except ValueError:
          pass

      if (selected_volume_identifier == u'all' or
          selected_volume_identifier in volume_identifiers):
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported partition identifier, please try again or abort '
          u'with Ctrl^C.\n'
          u'\n')

    return selected_volume_identifier

  def _PromptUserForVSSStoreIdentifiers(
      self, volume_system, volume_identifiers, vss_stores=None):
    """Prompts the user to provide the VSS store identifiers.

    This method first checks for the preferred VSS stores and falls back
    to prompt the user if no usable preferences were specified.

    Args:
      volume_system: The volume system (instance of dfvfs.VShadowVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.
      vss_stores: Optional list of preferred VSS store identifiers. The
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

    # TODO: refactor this to _GetVSSStoreIdentifiers.
    if vss_stores:
      if vss_stores == [u'all']:
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
            u'Identifier\tVSS store identifier\t\t\tCreation Time\n')

        for volume_identifier in volume_identifiers:
          volume = volume_system.GetVolumeByIdentifier(volume_identifier)
          if not volume:
            raise errors.SourceScannerError(
                u'Volume missing for identifier: {0:s}.'.format(
                    volume_identifier))

          vss_identifier = volume.GetAttribute(u'identifier')
          vss_creation_time = volume.GetAttribute(u'creation_time')
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
          u'as: 1,3..5. The first store is 1. All stores can be defined\n'
          u'as "all". If no stores are specified none will be processed. You\n'
          u'can abort with Ctrl^C.\n')

      selected_vss_stores = self._input_reader.Read()

      selected_vss_stores = selected_vss_stores.strip()
      if not selected_vss_stores:
        break

      try:
        selected_vss_stores = self._ParseVSSStoresString(selected_vss_stores)
      except errors.BadConfigOption:
        selected_vss_stores = []

      if selected_vss_stores == [u'all']:
        # We need to set the stores to cover all vss stores.
        selected_vss_stores = range(1, volume_system.number_of_volumes + 1)

      if not set(selected_vss_stores).difference(normalized_volume_identifiers):
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported VSS identifier(s), please try again or abort with '
          u'Ctrl^C.\n'
          u'\n')

    return selected_vss_stores

  def _ScanVolume(self, volume_scan_node):
    """Scans the volume scan node for volume and file systems.

    Args:
      volume_scan_node: the volume scan node (instance of dfvfs.ScanNode).

    Raises:
      SourceScannerError: if the format of or within the source
                          is not supported or the the scan node is invalid.
    """
    if not volume_scan_node or not volume_scan_node.path_spec:
      raise errors.SourceScannerError(u'Invalid or missing volume scan node.')

    # Get the first node where where we need to decide what to process.
    scan_node = volume_scan_node
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    # The source scanner found an encrypted volume and we need
    # a credential to unlock the volume.
    if scan_node.type_indicator in (
        dfvfs_definitions.ENCRYPTED_VOLUME_TYPE_INDICATORS):
      # TODO: ask for credentials to unlock volume.
      logging.warning(u'Encrypted volume not yet supported.')

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
      if self._process_vss:
        vss_store_identifiers = self._GetVSSStoreIdentifiers(
            scan_node, vss_stores=self._vss_stores)

        self._vss_stores = vss_store_identifiers
        for vss_store_identifier in vss_store_identifiers:
          location = u'/vss{0:d}'.format(vss_store_identifier)
          sub_scan_node = scan_node.GetSubNodeByLocation(location)
          path_spec = path_spec_factory.Factory.NewPathSpec(
              dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
              parent=sub_scan_node.path_spec)
          self._source_path_specs.append(path_spec)

      # TODO: move the TSK current volume scan node to the same level as
      # the VSS scan node.
      for sub_scan_node in scan_node.sub_nodes:
        if sub_scan_node.type_indicator == (
            dfvfs_definitions.TYPE_INDICATOR_TSK):
          self._source_path_specs.append(sub_scan_node.path_spec)

    # TODO: replace check with dfvfs_definitions.FILE_SYSTEM_TYPE_INDICATORS.
    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
      self._source_path_specs.append(scan_node.path_spec)

  def AddFilterOptions(self, argument_group):
    """Adds the filter options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'-f', u'--file_filter', u'--file-filter', dest=u'file_filter',
        action=u'store', type=unicode, default=None, help=(
            u'List of files to include for targeted collection of files to '
            u'parse, one line per file path, setup is /path|file - where each '
            u'element can contain either a variable set in the preprocessing '
            u'stage or a regular expression.'))

  def AddStorageMediaImageOptions(self, argument_group):
    """Adds the storage media image options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--partition', dest=u'partition_number', action=u'store', type=str,
        default=None, help=(
            u'Choose a partition number from a disk image. This partition '
            u'number should correspond to the partition number on the disk '
            u'image, starting from partition 1. All partitions can be '
            u'defined as: "all".'))

    argument_group.add_argument(
        u'-o', u'--offset', dest=u'image_offset', action=u'store', default=None,
        type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of sectors. A sector is {0:d} bytes in size by default '
            u'this can be overwritten with the --sector_size option.').format(
                self._DEFAULT_BYTES_PER_SECTOR))

    argument_group.add_argument(
        u'--sector_size', u'--sector-size', dest=u'bytes_per_sector',
        action=u'store', type=int, default=self._DEFAULT_BYTES_PER_SECTOR,
        help=(
            u'The number of bytes per sector, which is {0:d} by '
            u'default.').format(self._DEFAULT_BYTES_PER_SECTOR))

    argument_group.add_argument(
        u'--ob', u'--offset_bytes', u'--offset_bytes',
        dest=u'image_offset_bytes', action=u'store', default=None, type=int,
        help=(
            u'The offset of the volume within the storage media image in '
            u'number of bytes.'))

  def AddVSSProcessingOptions(self, argument_group):
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
            u'processed. A range of stores can be defined as: "3..5". '
            u'Multiple stores can be defined as: "1,3,5" (a list of comma '
            u'separated values). Ranges and lists can also be combined as: '
            u'"1,3..5". The first store is 1. All stores can be defined as: '
            u'"all".'))

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(StorageMediaTool, self).ParseOptions(options)
    self._ParseStorageMediaImageOptions(options)
    self._ParseVSSProcessingOptions(options)

    self._source_path = getattr(options, self._SOURCE_OPTION, None)
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

  def ScanSource(self, front_end):
    """Scans the source path for volume and file systems.

    This functions sets the internal source path specification and source
    type values. The arguments provide the preferred source parameters
    but will be ignored if they are not relevant.

    Args:
      front_end: the storage media front-end (instance of StorageMediaFrontend).

    Raises:
      SourceScannerError: if the format of or within the source is
                          not supported.
    """
    try:
      scan_context = front_end.ScanSource(self._source_path)
    except errors.SourceScannerError:
      raise

    if scan_context.source_type not in [
        scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      scan_node = scan_context.GetRootScanNode()
      self._source_path_specs.append(scan_node.path_spec)
      return

    # Get the first node where where we need to decide what to process.
    scan_node = scan_context.GetRootScanNode()
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    # The source scanner found a partition table and we need to determine
    # which partition needs to be processed.
    if scan_node.type_indicator not in [
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION]:
      partition_identifiers = None
    else:
      partition_identifiers = self._GetTSKPartitionIdentifiers(
          scan_node, partition_string=self._partition_string,
          partition_offset=self._partition_offset)

    if not partition_identifiers:
      self._ScanVolume(scan_node)

    else:
      for partition_identifier in partition_identifiers:
        location = u'/{0:s}'.format(partition_identifier)
        sub_scan_node = scan_node.GetSubNodeByLocation(location)
        self._ScanVolume(sub_scan_node)

    if not self._source_path_specs:
      raise errors.SourceScannerError(
          u'No supported file system found in source.')
