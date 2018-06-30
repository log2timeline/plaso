# -*- coding: utf-8 -*-
"""The storage media CLI tool."""

from __future__ import unicode_literals

import getpass
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

from plaso.cli import logger
from plaso.cli import tools
from plaso.cli import views
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
  _SOURCE_OPTION = 'source'

  _BINARY_DATA_CREDENTIAL_TYPES = ['key_data']

  _SUPPORTED_CREDENTIAL_TYPES = [
      'key_data', 'password', 'recovery_password', 'startup_key']

  # For context see: http://en.wikipedia.org/wiki/Byte
  _UNITS_1000 = ['B', 'kB', 'MB', 'GB', 'TB', 'EB', 'ZB', 'YB']
  _UNITS_1024 = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'EiB', 'ZiB', 'YiB']

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
    self._custom_artifacts_path = None
    self._artifact_definitions_path = None
    self._artifact_filters = None
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
      size_string_1000 = '{0:.1f}{1:s}'.format(
          size_1000, self._UNITS_1000[magnitude_1000])

    size_string_1024 = None
    if magnitude_1024 > 0 and magnitude_1024 <= 7:
      size_string_1024 = '{0:.1f}{1:s}'.format(
          size_1024, self._UNITS_1024[magnitude_1024])

    if not size_string_1000 or not size_string_1024:
      return '{0:d} B'.format(size)

    return '{0:s} / {1:s} ({2:d} B)'.format(
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
            'Volume missing for identifier: {0:s}.'.format(volume_identifier))

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
            'Volume missing for identifier: {0:s}.'.format(volume_identifier))

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
      partitions (Optional[list[str]]): preferred partition identifiers.

    Returns:
      list[str]: partition identifiers.

    Raises:
      RuntimeError: if the volume for a specific identifier cannot be
          retrieved.
      SourceScannerError: if the format of or within the source
          is not supported or the the scan node is invalid.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid scan node.')

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      self._output_writer.Write('[WARNING] No partitions found.\n')
      return None

    normalized_volume_identifiers = self._GetNormalizedTSKVolumeIdentifiers(
        volume_system, volume_identifiers)

    if partitions:
      if partitions == ['all']:
        partitions = range(1, volume_system.number_of_volumes + 1)

      if not set(partitions).difference(normalized_volume_identifiers):
        return [
            'p{0:d}'.format(partition_number)
            for partition_number in partitions]

    if partition_offset is not None:
      for volume in volume_system.volumes:
        volume_extent = volume.extents[0]
        if volume_extent.offset == partition_offset:
          return [volume.identifier]

      self._output_writer.Write((
          '[WARNING] No such partition with offset: {0:d} '
          '(0x{0:08x}).\n').format(partition_offset))

    if len(volume_identifiers) == 1:
      return volume_identifiers

    try:
      selected_volume_identifier = self._PromptUserForPartitionIdentifier(
          volume_system, volume_identifiers)
    except KeyboardInterrupt:
      raise errors.UserAbort('File system scan aborted.')

    if selected_volume_identifier == 'all':
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
      raise errors.SourceScannerError('Invalid scan node.')

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
      raise errors.UserAbort('File system scan aborted.')

    return selected_store_identifiers

  def _ParseCredentialOptions(self, options):
    """Parses the credential options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    credentials = getattr(options, 'credentials', [])
    if not isinstance(credentials, list):
      raise errors.BadConfigOption('Unsupported credentials value.')

    for credential_string in credentials:
      credential_type, _, credential_data = credential_string.partition(':')
      if not credential_type or not credential_data:
        raise errors.BadConfigOption(
            'Badly formatted credential: {0:s}.'.format(credential_string))

      if credential_type not in self._SUPPORTED_CREDENTIAL_TYPES:
        raise errors.BadConfigOption(
            'Unsupported credential type for: {0:s}.'.format(
                credential_string))

      if credential_type in self._BINARY_DATA_CREDENTIAL_TYPES:
        try:
          credential_data = credential_data.decode('hex')
        except TypeError:
          raise errors.BadConfigOption(
              'Unsupported credential data for: {0:s}.'.format(
                  credential_string))

      self._credentials.append((credential_type, credential_data))

  def _ParsePartitionsString(self, partitions):
    """Parses the user specified partitions string.

    Args:
      partitions (str): partitions. A range of partitions can be defined
          as: "3..5". Multiple partitions can be defined as: "1,3,5" (a list
          of comma separated values). Ranges and lists can also be combined
          as: "1,3..5". The first partition is 1. All partitions can be
          defined as: "all".

    Returns:
      list[int|str]: partition numbers or "all" to represent all available
          partitions.

    Raises:
      BadConfigOption: if the partitions string is invalid.
    """
    if not partitions:
      return []

    if partitions == 'all':
      return ['all']

    partition_numbers = []
    for partition_range in partitions.split(','):
      # Determine if the range is formatted as 1..3 otherwise it indicates
      # a single partition number.
      if '..' in partition_range:
        first_partition, last_partition = partition_range.split('..')
        try:
          first_partition = int(first_partition, 10)
          last_partition = int(last_partition, 10)
        except ValueError:
          raise errors.BadConfigOption(
              'Invalid partition range: {0:s}.'.format(partition_range))

        for partition_number in range(first_partition, last_partition + 1):
          if partition_number not in partition_numbers:
            partition_numbers.append(partition_number)
      else:
        if partition_range.startswith('p'):
          partition_range = partition_range[1:]

        try:
          partition_number = int(partition_range, 10)
        except ValueError:
          raise errors.BadConfigOption(
              'Invalid partition range: {0:s}.'.format(partition_range))

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
      raise errors.BadConfigOption('Missing source path.')

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
    partitions = getattr(options, 'partitions', None)
    self._partitions = self._ParsePartitionsString(partitions)

    partition = getattr(options, 'partition', None)

    if self._partitions and partition is not None:
      raise errors.BadConfigOption((
          'Option "--partition" can not be used in combination '
          'with "--partitions".'))

    if not self._partitions and partition is not None:
      self._partitions = self._ParsePartitionsString(partition)

    image_offset_bytes = getattr(options, 'image_offset_bytes', None)

    if self._partitions and image_offset_bytes is not None:
      raise errors.BadConfigOption((
          'Option "--image_offset_bytes" can not be used in combination '
          'with "--partitions" or "--partition".'))

    image_offset = getattr(options, 'image_offset', None)

    if self._partitions and image_offset is not None:
      raise errors.BadConfigOption((
          'Option "--image_offset" can not be used in combination with '
          '"--partitions" or "--partition".'))

    if (image_offset_bytes is not None and
        isinstance(image_offset_bytes, py2to3.STRING_TYPES)):
      try:
        image_offset_bytes = int(image_offset_bytes, 10)
      except ValueError:
        raise errors.BadConfigOption(
            'Invalid image offset bytes: {0:s}.'.format(image_offset_bytes))

    if image_offset_bytes is None and image_offset is not None:
      bytes_per_sector = getattr(
          options, 'bytes_per_sector', self._DEFAULT_BYTES_PER_SECTOR)

      if isinstance(image_offset, py2to3.STRING_TYPES):
        try:
          image_offset = int(image_offset, 10)
        except ValueError:
          raise errors.BadConfigOption(
              'Invalid image offset: {0:s}.'.format(image_offset))

      if isinstance(bytes_per_sector, py2to3.STRING_TYPES):
        try:
          bytes_per_sector = int(bytes_per_sector, 10)
        except ValueError:
          raise errors.BadConfigOption(
              'Invalid bytes per sector: {0:s}.'.format(bytes_per_sector))

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

    self._process_vss = not getattr(options, 'no_vss', True)
    if self._process_vss:
      vss_only = getattr(options, 'vss_only', False)
      vss_stores = getattr(options, 'vss_stores', None)

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

    if vss_stores == 'all':
      return ['all']

    store_numbers = []
    for vss_store_range in vss_stores.split(','):
      # Determine if the range is formatted as 1..3 otherwise it indicates
      # a single store number.
      if '..' in vss_store_range:
        first_store, last_store = vss_store_range.split('..')
        try:
          first_store = int(first_store, 10)
          last_store = int(last_store, 10)
        except ValueError:
          raise errors.BadConfigOption(
              'Invalid VSS store range: {0:s}.'.format(vss_store_range))

        for store_number in range(first_store, last_store + 1):
          if store_number not in store_numbers:
            store_numbers.append(store_number)
      else:
        if vss_store_range.startswith('vss'):
          vss_store_range = vss_store_range[3:]

        try:
          store_number = int(vss_store_range, 10)
        except ValueError:
          raise errors.BadConfigOption(
              'Invalid VSS store range: {0:s}.'.format(vss_store_range))

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
      self._output_writer.Write('Found a BitLocker encrypted volume.\n')
    else:
      self._output_writer.Write('Found an encrypted volume.\n')

    credentials_list = list(credentials.CREDENTIALS)
    credentials_list.append('skip')

    self._output_writer.Write('Supported credentials:\n')
    self._output_writer.Write('\n')
    for index, name in enumerate(credentials_list):
      self._output_writer.Write('  {0:d}. {1:s}\n'.format(index, name))
    self._output_writer.Write('\nNote that you can abort with Ctrl^C.\n\n')

    result = False
    while not result:
      self._output_writer.Write('Select a credential to unlock the volume: ')
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
              'Unsupported credential: {0:s}\n'.format(input_line))
          continue

      if credential_type == 'skip':
        break

      getpass_string = 'Enter credential data: '
      if sys.platform.startswith('win') and sys.version_info[0] < 3:
        # For Python 2 on Windows getpass (win_getpass) requires an encoded
        # byte string. For Python 3 we need it to be a Unicode string.
        getpass_string = self._EncodeString(getpass_string)

      credential_data = getpass.getpass(getpass_string)
      self._output_writer.Write('\n')

      if credential_type in self._BINARY_DATA_CREDENTIAL_TYPES:
        try:
          credential_data = credential_data.decode('hex')
        except TypeError:
          self._output_writer.Write('Unsupported credential data.\n')
          continue

      try:
        result = self._source_scanner.Unlock(
            scan_context, locked_scan_node.path_spec, credential_type,
            credential_data)

      except IOError as exception:
        logger.debug('Unable to unlock volume with error: {0!s}'.format(
            exception))
        result = False

      if not result:
        self._output_writer.Write('Unable to unlock volume.\n')
        self._output_writer.Write('\n')

    self._output_writer.Write('\n')

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
      str: partition identifier or "all".

    Raises:
      SourceScannerError: if the source cannot be processed.
    """
    self._output_writer.Write('The following partitions were found:\n')

    table_view = views.CLITabularTableView(column_names=[
        'Identifier', 'Offset (in bytes)', 'Size (in bytes)'])

    for volume_identifier in sorted(volume_identifiers):
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.SourceScannerError(
            'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      volume_extent = volume.extents[0]
      volume_offset = '{0:d} (0x{0:08x})'.format(volume_extent.offset)
      volume_size = self._FormatHumanReadableSize(volume_extent.size)

      table_view.AddRow([volume.identifier, volume_offset, volume_size])

    self._output_writer.Write('\n')
    table_view.Write(self._output_writer)
    self._output_writer.Write('\n')

    while True:
      self._output_writer.Write(
          'Please specify the identifier of the partition that should be '
          'processed.\nAll partitions can be defined as: "all". Note that you '
          'can abort with Ctrl^C.\n')

      selected_volume_identifier = self._input_reader.Read()
      selected_volume_identifier = selected_volume_identifier.strip()

      if not selected_volume_identifier.startswith('p'):
        try:
          partition_number = int(selected_volume_identifier, 10)
          selected_volume_identifier = 'p{0:d}'.format(partition_number)
        except ValueError:
          pass

      if (selected_volume_identifier == 'all' or
          selected_volume_identifier in volume_identifiers):
        break

      self._output_writer.Write(
          '\n'
          'Unsupported partition identifier, please try again or abort '
          'with Ctrl^C.\n'
          '\n')

    self._output_writer.Write('\n')
    return selected_volume_identifier

  def _PromptUserForVSSCurrentVolume(self):
    """Prompts the user if the current volume with VSS should be processed.

    Returns:
      bool: True if the current volume with VSS should be processed.
    """
    while True:
      self._output_writer.Write(
          'Volume Shadow Snapshots (VSS) were selected also process current\n'
          'volume? [yes, no]\n')

      process_current_volume = self._input_reader.Read()
      process_current_volume = process_current_volume.strip()
      process_current_volume = process_current_volume.lower()

      if (not process_current_volume or
          process_current_volume in ('no', 'yes')):
        break

      self._output_writer.Write(
          '\n'
          'Unsupported option, please try again or abort with Ctrl^C.\n'
          '\n')

    self._output_writer.Write('\n')
    return not process_current_volume or process_current_volume == 'yes'

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
      if vss_stores == ['all']:
        # We need to set the stores to cover all vss stores.
        vss_stores = range(1, volume_system.number_of_volumes + 1)

      if not set(vss_stores).difference(normalized_volume_identifiers):
        return vss_stores

    print_header = True
    while True:
      if print_header:
        self._output_writer.Write(
            'The following Volume Shadow Snapshots (VSS) were found:\n')

        table_view = views.CLITabularTableView(column_names=[
            'Identifier', 'Creation Time'])

        for volume_identifier in volume_identifiers:
          volume = volume_system.GetVolumeByIdentifier(volume_identifier)
          if not volume:
            raise errors.SourceScannerError(
                'Volume missing for identifier: {0:s}.'.format(
                    volume_identifier))

          vss_creation_time = volume.GetAttribute('creation_time')
          filetime = dfdatetime_filetime.Filetime(
              timestamp=vss_creation_time.value)
          vss_creation_time = filetime.GetPlasoTimestamp()
          vss_creation_time = timelib.Timestamp.CopyToIsoFormat(
              vss_creation_time)

          if volume.HasExternalData():
            vss_creation_time = (
                '{0:s}\tWARNING: data stored outside volume').format(
                    vss_creation_time)

          table_view.AddRow([volume.identifier, vss_creation_time])

        self._output_writer.Write('\n')
        table_view.Write(self._output_writer)
        self._output_writer.Write('\n')

        print_header = False

      self._output_writer.Write(
          'Please specify the identifier(s) of the VSS that should be '
          'processed:\nNote that a range of stores can be defined as: 3..5. '
          'Multiple stores can\nbe defined as: 1,3,5 (a list of comma '
          'separated values). Ranges and lists can\nalso be combined '
          'as: 1,3..5. The first store is 1. All stores can be defined\n'
          'as "all". If no stores are specified none will be processed. You\n'
          'can abort with Ctrl^C.\n')

      selected_vss_stores = self._input_reader.Read()

      selected_vss_stores = selected_vss_stores.strip()
      if not selected_vss_stores:
        return []

      try:
        selected_vss_stores = self._ParseVSSStoresString(selected_vss_stores)
      except errors.BadConfigOption:
        selected_vss_stores = []

      if selected_vss_stores == ['all']:
        # We need to set the stores to cover all vss stores.
        selected_vss_stores = range(1, volume_system.number_of_volumes + 1)

      if not set(selected_vss_stores).difference(normalized_volume_identifiers):
        break

      self._output_writer.Write(
          '\n'
          'Unsupported VSS identifier(s), please try again or abort with '
          'Ctrl^C.\n'
          '\n')

    self._output_writer.Write('\n')
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
      raise errors.SourceScannerError('Invalid or missing volume scan node.')

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
      raise errors.SourceScannerError('Invalid or missing volume scan node.')

    # Get the first node where where we need to decide what to process.
    scan_node = volume_scan_node
    while len(scan_node.sub_nodes) == 1:
      # Make sure that we prompt the user about VSS selection.
      if scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
        location = getattr(scan_node.path_spec, 'location', None)
        if location == '/':
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
            '[WARNING] Unable to unlock encrypted volume using the provided '
            'credentials.\n\n')

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
    location = getattr(volume_scan_node.path_spec, 'location', None)
    if location != '/':
      return

    vss_store_identifiers = self._GetVSSStoreIdentifiers(
        volume_scan_node, vss_stores=self._vss_stores)

    selected_vss_stores.extend(vss_store_identifiers)

    # Process VSS stores starting with the most recent one.
    vss_store_identifiers.reverse()
    for vss_store_identifier in vss_store_identifiers:
      location = '/vss{0:d}'.format(vss_store_identifier)
      sub_scan_node = volume_scan_node.GetSubNodeByLocation(location)
      if not sub_scan_node:
        logger.error(
            'Scan node missing for VSS store identifier: {0:d}.'.format(
                vss_store_identifier))
        continue

      # We "optimize" here for user experience, ideally we would scan for
      # a file system instead of hard coding a TSK child path specification.
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
          parent=sub_scan_node.path_spec)
      self._source_path_specs.append(path_spec)

  def AddCredentialOptions(self, argument_group):
    """Adds the credential options to the argument group.

    The credential options are use to unlock encrypted volumes.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--credential', action='append', default=[], type=str,
        dest='credentials', metavar='TYPE:DATA', help=(
            'Define a credentials that can be used to unlock encrypted '
            'volumes e.g. BitLocker. The credential is defined as type:data '
            'e.g. "password:BDE-test". Supported credential types are: '
            '{0:s}. Binary key data is expected to be passed in BASE-16 '
            'encoding (hexadecimal). WARNING credentials passed via command '
            'line arguments can end up in logs, so use this option with '
            'care.').format(', '.join(self._SUPPORTED_CREDENTIAL_TYPES)))

  def AddStorageMediaImageOptions(self, argument_group):
    """Adds the storage media image options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--partition', dest='partition', action='store', type=str,
        default=None, help=(
            'Choose a partition number from a disk image. This partition '
            'number should correspond to the partition number on the disk '
            'image, starting from partition 1. All partitions can be '
            'defined as: "all".'))

    argument_group.add_argument(
        '--partitions', dest='partitions', action='store', type=str,
        default=None, help=(
            'Define partitions that need to be processed. A range of '
            'partitions can be defined as: "3..5". Multiple partitions can '
            'be defined as: "1,3,5" (a list of comma separated values). '
            'Ranges and lists can also be combined as: "1,3..5". The first '
            'partition is 1. All partitions can be defined as: "all".'))

    argument_group.add_argument(
        '--offset', dest='image_offset', action='store', default=None,
        type=int, help=(
            'The offset of the volume within the storage media image in '
            'number of sectors. A sector is {0:d} bytes in size by default '
            'this can be overwritten with the --sector_size option.').format(
                self._DEFAULT_BYTES_PER_SECTOR))

    argument_group.add_argument(
        '--ob', '--offset_bytes', '--offset_bytes',
        dest='image_offset_bytes', action='store', default=None, type=int,
        help=(
            'The offset of the volume within the storage media image in '
            'number of bytes.'))

    argument_group.add_argument(
        '--sector_size', '--sector-size', dest='bytes_per_sector',
        action='store', type=int, default=self._DEFAULT_BYTES_PER_SECTOR,
        help=(
            'The number of bytes per sector, which is {0:d} by '
            'default.').format(self._DEFAULT_BYTES_PER_SECTOR))

  def AddVSSProcessingOptions(self, argument_group):
    """Adds the VSS processing options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--no_vss', '--no-vss', dest='no_vss', action='store_true',
        default=False, help=(
            'Do not scan for Volume Shadow Snapshots (VSS). This means that '
            'Volume Shadow Snapshots (VSS) are not processed.'))

    argument_group.add_argument(
        '--vss_only', '--vss-only', dest='vss_only', action='store_true',
        default=False, help=(
            'Do not process the current volume if Volume Shadow Snapshots '
            '(VSS) have been selected.'))

    argument_group.add_argument(
        '--vss_stores', '--vss-stores', dest='vss_stores', action='store',
        type=str, default=None, help=(
            'Define Volume Shadow Snapshots (VSS) (or stores that need to be '
            'processed. A range of stores can be defined as: "3..5". '
            'Multiple stores can be defined as: "1,3,5" (a list of comma '
            'separated values). Ranges and lists can also be combined as: '
            '"1,3..5". The first store is 1. All stores can be defined as: '
            '"all".'))

  def ScanSource(self, source_path):
    """Scans the source path for volume and file systems.

    This function sets the internal source path specification and source
    type values.

    Args:
      source_path (str): path to the source.

    Returns:
      dfvfs.SourceScannerContext: source scanner context.

    Raises:
      SourceScannerError: if the format of or within the source is
          not supported.
    """
    # Symbolic links are resolved here and not earlier to preserve the user
    # specified source path in storage and reporting.
    if os.path.islink(source_path):
      source_path = os.path.realpath(source_path)

    if (not source_path.startswith('\\\\.\\') and
        not os.path.exists(source_path)):
      raise errors.SourceScannerError(
          'No such device, file or directory: {0:s}.'.format(source_path))

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(source_path)

    try:
      self._source_scanner.Scan(scan_context)
    except (dfvfs_errors.BackEndError, ValueError) as exception:
      raise errors.SourceScannerError(
          'Unable to scan source with error: {0!s}.'.format(exception))

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
        location = '/{0:s}'.format(partition_identifier)
        sub_scan_node = scan_node.GetSubNodeByLocation(location)
        self._ScanVolume(scan_context, sub_scan_node)

    if not self._source_path_specs:
      raise errors.SourceScannerError(
          'No supported file system found in source.')

    return scan_context
