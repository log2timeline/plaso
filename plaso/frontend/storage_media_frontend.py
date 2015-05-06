# -*- coding: utf-8 -*-
"""The storage media front-end."""

import logging
import os

from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import context
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.frontend import frontend
from plaso.lib import errors
from plaso.lib import timelib


class StorageMediaFrontend(frontend.Frontend):
  """Class that implements a front-end with storage media support."""

  # For context see: http://en.wikipedia.org/wiki/Byte
  _UNITS_1000 = [u'B', u'kB', u'MB', u'GB', u'TB', u'EB', u'ZB', u'YB']
  _UNITS_1024 = [u'B', u'KiB', u'MiB', u'GiB', u'TiB', u'EiB', u'ZiB', u'YiB']

  def __init__(self):
    """Initializes the front-end object."""
    # TODO: remove the need to pass input_reader and output_writer.
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(StorageMediaFrontend, self).__init__(input_reader, output_writer)
    self._resolver_context = context.Context()
    self._scan_context = source_scanner.SourceScannerContext()
    self._source_path = None
    self._source_scanner = source_scanner.SourceScanner()

    # TODO: move this into a source handler to support multiple sources.
    self.partition_offset = None
    self.process_vss = True
    self.vss_stores = None

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
      self.vss_stores = self._GetVssStoreIdentifiersFromUser(
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
      if len(vss_stores) == 1 and vss_stores[0] == u'all':
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
          u'as: 1,3..5. The first store is 1. All stores can be defined as: '
          u'\'all\'.\nIf no stores are specified none will be processed.\n'
          u'You can abort with Ctrl^C.\n')

      selected_vss_stores = self._input_reader.Read()

      selected_vss_stores = selected_vss_stores.strip()
      if not selected_vss_stores:
        break

      try:
        selected_vss_stores = StorageMediaFrontend.ParseVssStores(
            selected_vss_stores)
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

  # TODO: remove this when support to handle multiple partitions is added.
  def GetSourcePathSpec(self):
    """Retrieves the source path specification.

    Returns:
      The source path specification (instance of dfvfs.PathSpec) or None.
    """
    if self._scan_context and self._scan_context.last_scan_node:
      return self._scan_context.last_scan_node.path_spec

  @classmethod
  def ParseVssStores(cls, vss_stores):
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

  def ScanSource(
      self, source_path, partition_number=None, partition_offset=None,
      enable_vss=False, vss_stores=None):
    """Scans the source path for volume and file systems.

    This functions sets the internal source path specification and source
    type values. The arguments provide the preferred source parameters
    but will be ignored if they are not relevant.

    Args:
      source_path: the path of the source device, directory or file.
      partition_number: optional preferred partition number.
                        The default is None.
      partition_offset: optional preferred partition offset in bytes.
                        The default is None.
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
    if (not source_path.startswith(u'\\\\.\\') and
        not os.path.exists(source_path)):
      raise errors.SourceScannerError(
          u'No such device, file or directory: {0:s}.'.format(source_path))

    # Use the dfVFS source scanner to do the actual scanning.
    scan_path_spec = None

    self._scan_context.OpenSourcePath(source_path)

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
                source_path))

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

        self.partition_offset = getattr(
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
                source_path))

    self._source_type = self._scan_context.source_type

    if self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:

      if self._scan_context.last_scan_node.type_indicator not in [
          dfvfs_definitions.TYPE_INDICATOR_TSK]:
        logging.warning(
            u'Unsupported file system falling back to single file mode.')
        self._source_type = self._scan_context.source_type

      elif self.partition_offset is None:
        self.partition_offset = 0

    # TODO: remove the need for this.
    self._source_path = source_path

    self.process_vss = enable_vss

  def SourceIsDirectory(self):
    """Determines if the source is a directory.

    Returns:
      True if the source is a directory, False if not.
    """
    return self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_DIRECTORY]

  def SourceIsFile(self):
    """Determines if the source is a file.

    Returns:
      True if the source is a file, False if not.
    """
    return self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_FILE]

  def SourceIsStorageMediaImage(self):
    """Determines if the source is a storage media image.

    Returns:
      True if the source is a storage media image, False if not.
    """
    return self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]
