# -*- coding: utf-8 -*-
"""The storage media CLI tool."""

import getpass
import logging
import os
import sys

from dfdatetime import filetime as dfdatetime_filetime
from dfvfs.analyzer import analyzer as dfvfs_analyzer
from dfvfs.analyzer import fvde_analyzer_helper
from dfvfs.credentials import manager as credentials_manager
from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import tools
from plaso.engine import configurations
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.lib import timelib


try:
  # Disable experimental FVDE support.
  dfvfs_analyzer.Analyzer.DeregisterHelper(
      fvde_analyzer_helper.FVDEAnalyzerHelper())
except KeyError:
  pass


class StorageMediaTool(tools.CLITool):
  """Class that implements a storage media CLI tool."""

  _DEFAULT_BYTES_PER_SECTOR = 512

  # TODO: remove this redirect.
  _SOURCE_OPTION = u'source'

  _BINARY_DATA_CREDENTIAL_TYPES = [u'key_data']

  _SUPPORTED_CREDENTIAL_TYPES = [
      u'key_data', u'password', u'recovery_password', u'startup_key']

  # For context see: http://en.wikipedia.org/wiki/Byte
  _UNITS_1000 = [u'B', u'kB', u'MB', u'GB', u'TB', u'EB', u'ZB', u'YB']
  _UNITS_1024 = [u'B', u'KiB', u'MiB', u'GiB', u'TiB', u'EiB', u'ZiB', u'YiB']

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(StorageMediaTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._credentials = []
    self._credential_configurations = []
    self._filter_file = None
    self._partitions = None
    self._partition_offset = None
    self._process_vss = False
    self._source_scanner = source_scanner.SourceScanner()
    self._source_path = None
    self._source_path_specs = []
    self._vss_only = False
    self._vss_stores = None

  def _AddCredentialConfiguration(
      self, path_spec, credential_type, credential_data):
    """Adds a credential configuration.

    Args:
      path_spec (dfvfs.PathSpec): path specification.
      credential_type (str): credential type.
      credential_data (bytes): credential data.
    """
    credential_configuration = configurations.CredentialConfiguration(
        credential_data=credential_data, credential_type=credential_type,
        path_spec=path_spec)

    self._credential_configurations.append(credential_configuration)

  def _FormatHumanReadableSize(self, size):
    """Represents a number of bytes as a human readable string.

    Args:
      size (int): size in bytes.

    Returns:
      str: human readable string of the size.
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

  def _GetNormalizedTSKVolumeIdentifiers(
      self, volume_system, volume_identifiers):
    """Retrieves the normalized TSK volume identifiers.

    Args:
      volume_system (dfvfs.TSKVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Returns:
      list[int]: normalized volume identifiers.
    """
    normalized_volume_identifiers = []
    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.SourceScannerError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      try:
        volume_identifier = int(volume.identifier[1:], 10)
        normalized_volume_identifiers.append(volume_identifier)
      except ValueError:
        pass

    return normalized_volume_identifiers

  def _GetNormalizedVShadowVolumeIdentifiers(
      self, volume_system, volume_identifiers):
    """Retrieves the normalized VShadow volume identifiers.

    Args:
      volume_system (dfvfs.VShadowVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Returns:
      list[int]: normalized volume identifiers.
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

    return normalized_volume_identifiers

  # TODO: refactor this method that it become more clear what it is
  # supposed to do.
  def _GetTSKPartitionIdentifiers(
      self, scan_node, partition_offset=None, partitions=None):
    """Determines the TSK partition identifiers.

    This method first checks for the preferred partition number, then for
    the preferred partition offset and falls back to prompt the user if
    no usable preferences were specified.

    Args:
      scan_node (dfvfs.SourceScanNode): scan node.
      partition_offset (Optional[int]): preferred partition byte offset.
      paritions (Optional[list[str]]): preferred partition identifiers.

    Returns:
      list[str]: partition identifiers.

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

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      self._output_writer.Write(u'[WARNING] No partitions found.\n')
      return

    normalized_volume_identifiers = self._GetNormalizedTSKVolumeIdentifiers(
        volume_system, volume_identifiers)

    if partitions:
      if partitions == [u'all']:
        partitions = range(1, volume_system.number_of_volumes + 1)

      if not set(partitions).difference(normalized_volume_identifiers):
        return [
            u'p{0:d}'.format(partition_number)
            for partition_number in partitions]

    if partition_offset is not None:
      for volume in volume_system.volumes:
        volume_extent = volume.extents[0]
        if volume_extent.offset == partition_offset:
          return [volume.identifier]

      self._output_writer.Write((
          u'[WARNING] No such partition with offset: {0:d} '
          u'(0x{0:08x}).\n').format(partition_offset))

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
      scan_node (dfvfs.SourceScanNode): scan node.
      vss_stores (Optional[list[str]]): preferred VSS store identifiers.

    Returns:
      list[str] VSS store identifiers.

    Raises:
      SourceScannerError: if the format of or within the source
          is not supported or the the scan node is invalid.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError(u'Invalid scan node.')

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(scan_node.path_spec)

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

  def _ParseCredentialOptions(self, options):
    """Parses the credential options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    credentials = getattr(options, u'credentials', [])
    if not isinstance(credentials, list):
      raise errors.BadConfigOption(u'Unsupported credentials value.')

    for credential_string in credentials:
      credential_type, _, credential_data = credential_string.partition(u':')
      if not credential_type or not credential_data:
        raise errors.BadConfigOption(
            u'Badly formatted credential: {0:s}.'.format(credential_string))

      if credential_type not in self._SUPPORTED_CREDENTIAL_TYPES:
        raise errors.BadConfigOption(
            u'Unsupported credential type for: {0:s}.'.format(
                credential_string))

      if credential_type in self._BINARY_DATA_CREDENTIAL_TYPES:
        try:
          credential_data = credential_data.decode(u'hex')
        except TypeError:
          raise errors.BadConfigOption(
              u'Unsupported credential data for: {0:s}.'.format(
                  credential_string))

      self._credentials.append((credential_type, credential_data))

  def _ParsePartitionsString(self, partitions):
    """Parses the user specified partitions string.

    Args:
      partitions (str): partitions. A range of partitions can be defined
          as: "3..5". Multiple partitions can be defined as: "1,3,5" (a list
          of comma separated values). Ranges and lists can also be combined
          as: "1,3..5". The first partition is 1. All partition can be
          defined as: "all".

    Returns:
      list[str]: partitions.

    Raises:
      BadConfigOption: if the partitions option is invalid.
    """
    if not partitions:
      return []

    if partitions == u'all':
      return [u'all']

    partition_numbers = []
    for partition_range in partitions.split(u','):
      # Determine if the range is formatted as 1..3 otherwise it indicates
      # a single partition number.
      if u'..' in partition_range:
        first_partition, last_partition = partition_range.split(u'..')
        try:
          first_partition = int(first_partition, 10)
          last_partition = int(last_partition, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid partition range: {0:s}.'.format(partition_range))

        for partition_number in range(first_partition, last_partition + 1):
          if partition_number not in partition_numbers:
            partition_numbers.append(partition_number)
      else:
        if partition_range.startswith(u'p'):
          partition_range = partition_range[1:]

        try:
          partition_number = int(partition_range, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid partition range: {0:s}.'.format(partition_range))

        if partition_number not in partition_numbers:
          partition_numbers.append(partition_number)

    return sorted(partition_numbers)

  def _ParseSourcePathOption(self, options):
    """Parses the source path option.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._source_path = self.ParseStringOption(options, self._SOURCE_OPTION)
    if not self._source_path:
      raise errors.BadConfigOption(u'Missing source path.')

    self._source_path = os.path.abspath(self._source_path)

  def _ParseStorageMediaOptions(self, options):
    """Parses the storage media options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._ParseStorageMediaImageOptions(options)
    self._ParseVSSProcessingOptions(options)
    self._ParseCredentialOptions(options)
    self._ParseSourcePathOption(options)

  def _ParseStorageMediaImageOptions(self, options):
    """Parses the storage media image options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    partitions = getattr(options, u'partitions', None)
    self._partitions = self._ParsePartitionsString(partitions)

    partition = getattr(options, u'partition', None)

    if self._partitions and partition is not None:
      raise errors.BadConfigOption((
          u'Option "--partition" can not be used in combination '
          u'with "--partitions".'))

    if not self._partitions and partition is not None:
      self._partitions = self._ParsePartitionsString(partition)

    image_offset_bytes = getattr(options, u'image_offset_bytes', None)

    if self._partitions and image_offset_bytes is not None:
      raise errors.BadConfigOption((
          u'Option "--image_offset_bytes" can not be used in combination '
          u'with "--partitions" or "--partition".'))

    image_offset = getattr(options, u'image_offset', None)

    if self._partitions and image_offset is not None:
      raise errors.BadConfigOption((
          u'Option "--image_offset" can not be used in combination with '
          u'"--partitions" or "--partition".'))

    if (image_offset_bytes is not None and
        isinstance(image_offset_bytes, py2to3.STRING_TYPES)):
      try:
        image_offset_bytes = int(image_offset_bytes, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid image offset bytes: {0:s}.'.format(image_offset_bytes))

    if image_offset_bytes is None and image_offset is not None:
      bytes_per_sector = getattr(
          options, u'bytes_per_sector', self._DEFAULT_BYTES_PER_SECTOR)

      if isinstance(image_offset, py2to3.STRING_TYPES):
        try:
          image_offset = int(image_offset, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid image offset: {0:s}.'.format(image_offset))

      if isinstance(bytes_per_sector, py2to3.STRING_TYPES):
        try:
          bytes_per_sector = int(bytes_per_sector, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid bytes per sector: {0:s}.'.format(bytes_per_sector))

    if image_offset_bytes:
      self._partition_offset = image_offset_bytes
    elif image_offset:
      self._partition_offset = image_offset * bytes_per_sector

  def _ParseVSSProcessingOptions(self, options):
    """Parses the VSS processing options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    vss_only = False
    vss_stores = None

    self._process_vss = not getattr(options, u'no_vss', True)
    if self._process_vss:
      vss_only = getattr(options, u'vss_only', False)
      vss_stores = getattr(options, u'vss_stores', None)

    if vss_stores:
      vss_stores = self._ParseVSSStoresString(vss_stores)

    self._vss_only = vss_only
    self._vss_stores = vss_stores

  def _ParseVSSStoresString(self, vss_stores):
    """Parses the user specified VSS stores string.

    Args:
      vss_stores (str): VSS stores. A range of stores can be defined
          as: "3..5". Multiple stores can be defined as: "1,3,5" (a list
          of comma separated values). Ranges and lists can also be
          combined as: "1,3..5". The first store is 1. All stores can be
          defined as: "all".

    Returns:
      list[str]: VSS stores.

    Raises:
      BadConfigOption: if the VSS stores option is invalid.
    """
    if not vss_stores:
      return []

    if vss_stores == u'all':
      return [u'all']

    store_numbers = []
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
          if store_number not in store_numbers:
            store_numbers.append(store_number)
      else:
        if vss_store_range.startswith(u'vss'):
          vss_store_range = vss_store_range[3:]

        try:
          store_number = int(vss_store_range, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid VSS store range: {0:s}.'.format(vss_store_range))

        if store_number not in store_numbers:
          store_numbers.append(store_number)

    return sorted(store_numbers)

  def _PromptUserForEncryptedVolumeCredential(
      self, scan_context, locked_scan_node, credentials):
    """Prompts the user to provide a credential for an encrypted volume.

    Args:
      scan_context (dfvfs.SourceScannerContext): source scanner context.
      locked_scan_node (dfvfs.SourceScanNode): locked scan node.
      credentials (dfvfs.Credentials): credentials supported by the locked
          scan node.

    Returns:
      bool: True if the volume was unlocked.
    """
    # TODO: print volume description.
    if locked_scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_BDE:
      self._output_writer.Write(u'Found a BitLocker encrypted volume.\n')
    else:
      self._output_writer.Write(u'Found an encrypted volume.\n')

    credentials_list = list(credentials.CREDENTIALS)
    credentials_list.append(u'skip')

    self._output_writer.Write(u'Supported credentials:\n')
    self._output_writer.Write(u'\n')
    for index, name in enumerate(credentials_list):
      self._output_writer.Write(u'  {0:d}. {1:s}\n'.format(index, name))
    self._output_writer.Write(u'\nNote that you can abort with Ctrl^C.\n\n')

    result = False
    while not result:
      self._output_writer.Write(u'Select a credential to unlock the volume: ')
      # TODO: add an input reader.
      input_line = self._input_reader.Read()
      input_line = input_line.strip()

      if input_line in credentials_list:
        credential_type = input_line
      else:
        try:
          credential_type = int(input_line, 10)
          credential_type = credentials_list[credential_type]
        except (IndexError, ValueError):
          self._output_writer.Write(
              u'Unsupported credential: {0:s}\n'.format(input_line))
          continue

      if credential_type == u'skip':
        break

      getpass_string = u'Enter credential data: '
      if sys.platform.startswith(u'win') and sys.version_info[0] < 3:
        # For Python 2 on Windows getpass (win_getpass) requires an encoded
        # byte string. For Python 3 we need it to be a Unicode string.
        getpass_string = self._EncodeString(getpass_string)

      credential_data = getpass.getpass(getpass_string)
      self._output_writer.Write(u'\n')

      if credential_type in self._BINARY_DATA_CREDENTIAL_TYPES:
        try:
          credential_data = credential_data.decode(u'hex')
        except TypeError:
          self._output_writer.Write(u'Unsupported credential data.\n')
          continue

      try:
        result = self._source_scanner.Unlock(
            scan_context, locked_scan_node.path_spec, credential_type,
            credential_data)

      except IOError as exception:
        logging.debug(u'Unable to unlock volume with error: {0:s}'.format(
            exception))
        result = False

      if not result:
        self._output_writer.Write(u'Unable to unlock volume.\n')
        self._output_writer.Write(u'\n')

    self._output_writer.Write(u'\n')

    if result:
      self._AddCredentialConfiguration(
          locked_scan_node.path_spec, credential_type, credential_data)

    return result

  def _PromptUserForPartitionIdentifier(
      self, volume_system, volume_identifiers):
    """Prompts the user to provide a partition identifier.

    Args:
      volume_system (dfvfs.TSKVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Returns:
      str: partition identifier or 'all'.

    Raises:
      SourceScannerError: if the source cannot be processed.
    """
    self._output_writer.Write(
        u'The following partitions were found:\n'
        u'Identifier\tOffset (in bytes)\tSize (in bytes)\n')

    for volume_identifier in sorted(volume_identifiers):
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.SourceScannerError(
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

    self._output_writer.Write(u'\n')
    return selected_volume_identifier

  def _PromptUserForVSSCurrentVolume(self):
    """Prompts the user if the current volume with VSS should be processed.

    Returns:
      bool: True if the current volume with VSS should be processed.
    """
    while True:
      self._output_writer.Write(
          u'Volume Shadow Snapshots (VSS) were selected also process current\n'
          u'volume? [yes, no]\n')

      process_current_volume = self._input_reader.Read()
      process_current_volume = process_current_volume.strip()
      process_current_volume = process_current_volume.lower()

      if (not process_current_volume or
          process_current_volume in (u'no', u'yes')):
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported option, please try again or abort with Ctrl^C.\n'
          u'\n')

    self._output_writer.Write(u'\n')
    return not process_current_volume or process_current_volume == u'yes'

  def _PromptUserForVSSStoreIdentifiers(
      self, volume_system, volume_identifiers, vss_stores=None):
    """Prompts the user to provide the VSS store identifiers.

    This method first checks for the preferred VSS stores and falls back
    to prompt the user if no usable preferences were specified.

    Args:
      volume_system (dfvfs.VShadowVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.
      vss_stores (Optional[list[str]]): preferred VSS store identifiers.

    Returns:
      list[str]: selected VSS store identifiers.

    Raises:
      SourceScannerError: if the source cannot be processed.
    """
    normalized_volume_identifiers = self._GetNormalizedVShadowVolumeIdentifiers(
        volume_system, volume_identifiers)

    # TODO: refactor this to _GetVSSStoreIdentifiers.
    if vss_stores:
      if vss_stores == [u'all']:
        # We need to set the stores to cover all vss stores.
        vss_stores = range(1, volume_system.number_of_volumes + 1)

      if not set(vss_stores).difference(normalized_volume_identifiers):
        return vss_stores

    print_header = True
    while True:
      if print_header:
        self._output_writer.Write(
            u'The following Volume Shadow Snapshots (VSS) were found:\n'
            u'Identifier\t\tCreation Time\n')

        for volume_identifier in volume_identifiers:
          volume = volume_system.GetVolumeByIdentifier(volume_identifier)
          if not volume:
            raise errors.SourceScannerError(
                u'Volume missing for identifier: {0:s}.'.format(
                    volume_identifier))

          vss_creation_time = volume.GetAttribute(u'creation_time')
          filetime = dfdatetime_filetime.Filetime(
              timestamp=vss_creation_time.value)
          vss_creation_time = filetime.GetPlasoTimestamp()
          vss_creation_time = timelib.Timestamp.CopyToIsoFormat(
              vss_creation_time)

          if volume.HasExternalData():
            external_data = u'\tWARNING: data stored outside volume'
          else:
            external_data = u''

          self._output_writer.Write(u'{0:s}\t\t\t{1:s}{2:s}\n'.format(
              volume.identifier, vss_creation_time, external_data))

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
        return []

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

    self._output_writer.Write(u'\n')
    return selected_vss_stores

  def _ScanVolume(self, scan_context, volume_scan_node):
    """Scans the volume scan node for volume and file systems.

    Args:
      scan_context (dfvfs.SourceScannerContext): source scanner context.
      volume_scan_node (dfvfs.SourceScanNode): volume scan node.

    Raises:
      SourceScannerError: if the format of or within the source
          is not supported or the the scan node is invalid.
    """
    if not volume_scan_node or not volume_scan_node.path_spec:
      raise errors.SourceScannerError(u'Invalid or missing volume scan node.')

    selected_vss_stores = []
    if not volume_scan_node.sub_nodes:
      self._ScanVolumeScanNode(
          scan_context, volume_scan_node, selected_vss_stores)

    else:
      # Some volumes contain other volume or file systems e.g. BitLocker ToGo
      # has an encrypted and unencrypted volume.
      for sub_scan_node in volume_scan_node.sub_nodes:
        self._ScanVolumeScanNode(
            scan_context, sub_scan_node, selected_vss_stores)

  def _ScanVolumeScanNode(
      self, scan_context, volume_scan_node, selected_vss_stores):
    """Scans an individual volume scan node for volume and file systems.

    Args:
      scan_context (dfvfs.SourceScannerContext): source scanner context.
      volume_scan_node (dfvfs.SourceScanNode): volume scan node.
      selected_vss_stores (list[str]): selected VSS store identifiers.

    Raises:
      SourceScannerError: if the format of or within the source
          is not supported or the the scan node is invalid.
    """
    if not volume_scan_node or not volume_scan_node.path_spec:
      raise errors.SourceScannerError(u'Invalid or missing volume scan node.')

    # Get the first node where where we need to decide what to process.
    scan_node = volume_scan_node
    while len(scan_node.sub_nodes) == 1:
      # Make sure that we prompt the user about VSS selection.
      if scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
        location = getattr(scan_node.path_spec, u'location', None)
        if location == u'/':
          break

      scan_node = scan_node.sub_nodes[0]

    # The source scanner found an encrypted volume and we need
    # a credential to unlock the volume.
    if scan_node.type_indicator in (
        dfvfs_definitions.ENCRYPTED_VOLUME_TYPE_INDICATORS):
      self._ScanVolumeScanNodeEncrypted(scan_context, scan_node)

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
      self._ScanVolumeScanNodeVSS(scan_node, selected_vss_stores)

    elif scan_node.type_indicator in (
        dfvfs_definitions.FILE_SYSTEM_TYPE_INDICATORS):
      if (not self._vss_only or not selected_vss_stores or
          self._PromptUserForVSSCurrentVolume()):
        self._source_path_specs.append(scan_node.path_spec)

  def _ScanVolumeScanNodeEncrypted(self, scan_context, volume_scan_node):
    """Scans an encrypted volume scan node for volume and file systems.

    Args:
      scan_context (dfvfs.SourceScannerContext): source scanner context.
      volume_scan_node (dfvfs.SourceScanNode): volume scan node.
    """
    result = not scan_context.IsLockedScanNode(volume_scan_node.path_spec)
    if not result:
      credentials = credentials_manager.CredentialsManager.GetCredentials(
          volume_scan_node.path_spec)

      result = False
      for credential_type, credential_data in self._credentials:
        if credential_type not in credentials.CREDENTIALS:
          continue

        result = self._source_scanner.Unlock(
            scan_context, volume_scan_node.path_spec, credential_type,
            credential_data)

        if result:
          self._AddCredentialConfiguration(
              volume_scan_node.path_spec, credential_type, credential_data)
          break

      if self._credentials and not result:
        self._output_writer.Write(
            u'[WARNING] Unable to unlock encrypted volume using the provided '
            u'credentials.\n\n')

      if not result:
        result = self._PromptUserForEncryptedVolumeCredential(
            scan_context, volume_scan_node, credentials)

    if result:
      self._source_scanner.Scan(
          scan_context, scan_path_spec=volume_scan_node.path_spec)
      self._ScanVolume(scan_context, volume_scan_node)

  def _ScanVolumeScanNodeVSS(self, volume_scan_node, selected_vss_stores):
    """Scans a VSS volume scan node for volume and file systems.

    Args:
      scan_context (dfvfs.SourceScannerContext): source scanner context.
      volume_scan_node (dfvfs.SourceScanNode): volume scan node.
      selected_vss_stores (list[str]): selected VSS store identifiers.

    Raises:
      SourceScannerError: if a VSS sub scan node cannot be retrieved.
    """
    if not self._process_vss:
      return

    # Do not scan inside individual VSS store scan nodes.
    location = getattr(volume_scan_node.path_spec, u'location', None)
    if location != u'/':
      return

    vss_store_identifiers = self._GetVSSStoreIdentifiers(
        volume_scan_node, vss_stores=self._vss_stores)

    selected_vss_stores.extend(vss_store_identifiers)

    # Process VSS stores starting with the most recent one.
    vss_store_identifiers.reverse()
    for vss_store_identifier in vss_store_identifiers:
      location = u'/vss{0:d}'.format(vss_store_identifier)
      sub_scan_node = volume_scan_node.GetSubNodeByLocation(location)
      if not sub_scan_node:
        logging.error(
            u'Scan node missing for VSS store identifier: {0:d}.'.format(
                vss_store_identifier))
        continue

      # We "optimize" here for user experience, ideally we would scan for
      # a file system instead of hard coding a TSK child path specification.
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
          parent=sub_scan_node.path_spec)
      self._source_path_specs.append(path_spec)

  def AddCredentialOptions(self, argument_group):
    """Adds the credential options to the argument group.

    The credential options are use to unlock encrypted volumes.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--credential', action=u'append', default=[], type=str,
        dest=u'credentials', metavar=u'TYPE:DATA', help=(
            u'Define a credentials that can be used to unlock encrypted '
            u'volumes e.g. BitLocker. The credential is defined as type:data '
            u'e.g. "password:BDE-test". Supported credential types are: '
            u'{0:s}. Binary key data is expected to be passed in BASE-16 '
            u'encoding (hexadecimal). WARNING credentials passed via command '
            u'line arguments can end up in logs, so use this option with '
            u'care.').format(u', '.join(self._SUPPORTED_CREDENTIAL_TYPES)))

  def AddStorageMediaImageOptions(self, argument_group):
    """Adds the storage media image options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--partition', dest=u'partition', action=u'store', type=str,
        default=None, help=(
            u'Choose a partition number from a disk image. This partition '
            u'number should correspond to the partition number on the disk '
            u'image, starting from partition 1. All partitions can be '
            u'defined as: "all".'))

    argument_group.add_argument(
        u'--partitions', dest=u'partitions', action=u'store', type=str,
        default=None, help=(
            u'Define partitions that need to be processed. A range of '
            u'partitions can be defined as: "3..5". Multiple partitions can '
            u'be defined as: "1,3,5" (a list of comma separated values). '
            u'Ranges and lists can also be combined as: "1,3..5". The first '
            u'partition is 1. All partition can be defined as: "all".'))

    argument_group.add_argument(
        u'-o', u'--offset', dest=u'image_offset', action=u'store', default=None,
        type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of sectors. A sector is {0:d} bytes in size by default '
            u'this can be overwritten with the --sector_size option.').format(
                self._DEFAULT_BYTES_PER_SECTOR))

    argument_group.add_argument(
        u'--ob', u'--offset_bytes', u'--offset_bytes',
        dest=u'image_offset_bytes', action=u'store', default=None, type=int,
        help=(
            u'The offset of the volume within the storage media image in '
            u'number of bytes.'))

    argument_group.add_argument(
        u'--sector_size', u'--sector-size', dest=u'bytes_per_sector',
        action=u'store', type=int, default=self._DEFAULT_BYTES_PER_SECTOR,
        help=(
            u'The number of bytes per sector, which is {0:d} by '
            u'default.').format(self._DEFAULT_BYTES_PER_SECTOR))

  def AddVSSProcessingOptions(self, argument_group):
    """Adds the VSS processing options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--no_vss', u'--no-vss', dest=u'no_vss', action=u'store_true',
        default=False, help=(
            u'Do not scan for Volume Shadow Snapshots (VSS). This means that '
            u'Volume Shadow Snapshots (VSS) are not processed.'))

    argument_group.add_argument(
        u'--vss_only', u'--vss-only', dest=u'vss_only', action=u'store_true',
        default=False, help=(
            u'Do not process the current volume if Volume Shadow Snapshots '
            u'(VSS) have been selected.'))

    argument_group.add_argument(
        u'--vss_stores', u'--vss-stores', dest=u'vss_stores', action=u'store',
        type=str, default=None, help=(
            u'Define Volume Shadow Snapshots (VSS) (or stores that need to be '
            u'processed. A range of stores can be defined as: "3..5". '
            u'Multiple stores can be defined as: "1,3,5" (a list of comma '
            u'separated values). Ranges and lists can also be combined as: '
            u'"1,3..5". The first store is 1. All stores can be defined as: '
            u'"all".'))

  def ScanSource(self):
    """Scans the source path for volume and file systems.

    This function sets the internal source path specification and source
    type values.

    Returns:
      dfvfs.SourceScannerContext: source scanner context.

    Raises:
      SourceScannerError: if the format of or within the source is
          not supported.
    """
    if (not self._source_path.startswith(u'\\\\.\\') and
        not os.path.exists(self._source_path)):
      raise errors.SourceScannerError(
          u'No such device, file or directory: {0:s}.'.format(
              self._source_path))

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(self._source_path)

    try:
      self._source_scanner.Scan(scan_context)
    except (dfvfs_errors.BackEndError, ValueError) as exception:
      raise errors.SourceScannerError(
          u'Unable to scan source with error: {0:s}.'.format(exception))

    if scan_context.source_type not in (
        scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE):
      scan_node = scan_context.GetRootScanNode()
      self._source_path_specs.append(scan_node.path_spec)
      return scan_context

    # Get the first node where where we need to decide what to process.
    scan_node = scan_context.GetRootScanNode()
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    # The source scanner found a partition table and we need to determine
    # which partition needs to be processed.
    if scan_node.type_indicator != (
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
      partition_identifiers = None

    else:
      partition_identifiers = self._GetTSKPartitionIdentifiers(
          scan_node, partition_offset=self._partition_offset,
          partitions=self._partitions)

    if not partition_identifiers:
      self._ScanVolume(scan_context, scan_node)

    else:
      for partition_identifier in partition_identifiers:
        location = u'/{0:s}'.format(partition_identifier)
        sub_scan_node = scan_node.GetSubNodeByLocation(location)
        self._ScanVolume(scan_context, sub_scan_node)

    if not self._source_path_specs:
      raise errors.SourceScannerError(
          u'No supported file system found in source.')

    return scan_context
