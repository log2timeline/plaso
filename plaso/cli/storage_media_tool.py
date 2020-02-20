# -*- coding: utf-8 -*-
"""The storage media CLI tool."""

from __future__ import unicode_literals

import codecs
import getpass
import os
import sys
import textwrap

from dfdatetime import filetime as dfdatetime_filetime
from dfvfs.analyzer import analyzer as dfvfs_analyzer
from dfvfs.analyzer import fvde_analyzer_helper
from dfvfs.credentials import manager as credentials_manager
from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.volume import apfs_volume_system
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import tools
from plaso.cli import views
from plaso.engine import configurations
from plaso.lib import errors


try:
  # Disable experimental FVDE support.
  dfvfs_analyzer.Analyzer.DeregisterHelper(
      fvde_analyzer_helper.FVDEAnalyzerHelper())
except KeyError:
  pass


class StorageMediaTool(tools.CLITool):
  """CLI tool that supports a storage media device or image as input."""

  # TODO: remove this redirect.
  _SOURCE_OPTION = 'source'

  _BINARY_DATA_CREDENTIAL_TYPES = ['key_data']

  _SUPPORTED_CREDENTIAL_TYPES = [
      'key_data', 'password', 'recovery_password', 'startup_key']

  # For context see: http://en.wikipedia.org/wiki/Byte
  _UNITS_1000 = ['B', 'kB', 'MB', 'GB', 'TB', 'EB', 'ZB', 'YB']
  _UNITS_1024 = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'EiB', 'ZiB', 'YiB']

  _USER_PROMPT_APFS = (
      'Please specify the identifier(s) of the APFS volume that should be '
      'processed: Note that a range of volumes can be defined as: 3..5. '
      'Multiple volumes can be defined as: 1,3,5 (a list of comma separated '
      'values). Ranges and lists can also be combined as: 1,3..5. The first '
      'volume is 1. All volumes can be defined as "all". If no volumes are '
      'specified none will be processed. You can abort with Ctrl^C.')

  _USER_PROMPT_TSK = (
      'Please specify the identifier of the partition that should be '
      'processed. All partitions can be defined as: "all". Note that you can '
      'abort with Ctrl^C.')

  _USER_PROMPT_VSS = (
      'Please specify the identifier(s) of the VSS that should be processed: '
      'Note that a range of stores can be defined as: 3..5. Multiple stores '
      'can be defined as: 1,3,5 (a list of comma separated values). Ranges '
      'and lists can also be combined as: 1,3..5. The first store is 1. All '
      'stores can be defined as "all". If no stores are specified none will '
      'be processed. You can abort with Ctrl^C.')

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
    self._process_vss = False
    self._source_scanner = source_scanner.SourceScanner()
    self._source_path = None
    self._source_path_specs = []
    self._textwrapper = textwrap.TextWrapper()
    self._user_selected_vss_stores = False
    self._volumes = None
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
    if 0 < magnitude_1000 <= 7:
      size_string_1000 = '{0:.1f}{1:s}'.format(
          size_1000, self._UNITS_1000[magnitude_1000])

    size_string_1024 = None
    if 0 < magnitude_1024 <= 7:
      size_string_1024 = '{0:.1f}{1:s}'.format(
          size_1024, self._UNITS_1024[magnitude_1024])

    if not size_string_1000 or not size_string_1024:
      return '{0:d} B'.format(size)

    return '{0:s} / {1:s} ({2:d} B)'.format(
        size_string_1024, size_string_1000, size)

  def _GetAPFSVolumeIdentifiers(self, scan_node):
    """Determines the APFS volume identifiers.

    Args:
      scan_node (dfvfs.SourceScanNode): scan node.

    Returns:
      list[str]: APFS volume identifiers.

    Raises:
      SourceScannerError: if the format of or within the source is not
          supported or the the scan node is invalid.
      UserAbort: if the user requested to abort.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid scan node.')

    volume_system = apfs_volume_system.APFSVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      return []

    # TODO: refactor self._volumes to use scan options.
    if self._volumes:
      if self._volumes == 'all':
        volumes = range(1, volume_system.number_of_volumes + 1)
      else:
        volumes = self._ParseVolumeIdentifiersString(
            self._volumes, prefix='apfs')

      selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
          volume_system, volumes, prefix='apfs')

      if not set(selected_volume_identifiers).difference(volume_identifiers):
        return selected_volume_identifiers

    if len(volume_identifiers) > 1:
      try:
        volume_identifiers = self._PromptUserForAPFSVolumeIdentifiers(
            volume_system, volume_identifiers)
      except KeyboardInterrupt:
        raise errors.UserAbort('File system scan aborted.')

    return self._NormalizedVolumeIdentifiers(
        volume_system, volume_identifiers, prefix='apfs')

  def _GetTSKPartitionIdentifiers(self, scan_node):
    """Determines the TSK partition identifiers.

    This method first checks for the preferred partition number, then
    falls back to prompt the user if no usable preferences were specified.

    Args:
      scan_node (dfvfs.SourceScanNode): scan node.

    Returns:
      list[str]: TSK partition identifiers.

    Raises:
      RuntimeError: if the volume for a specific identifier cannot be
          retrieved.
      SourceScannerError: if the format of or within the source
          is not supported or the the scan node is invalid.
      UserAbort: if the user requested to abort.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid scan node.')

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      return []

    # TODO: refactor self._partitions to use scan options.
    if self._partitions:
      if self._partitions == 'all':
        partitions = range(1, volume_system.number_of_volumes + 1)
      else:
        partitions = self._ParseVolumeIdentifiersString(
            self._partitions, prefix='p')

      selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
          volume_system, partitions, prefix='p')

      if not set(selected_volume_identifiers).difference(volume_identifiers):
        return selected_volume_identifiers

    if len(volume_identifiers) == 1:
      return volume_identifiers

    try:
      volume_identifiers = self._PromptUserForPartitionIdentifiers(
          volume_system, volume_identifiers)
    except KeyboardInterrupt:
      raise errors.UserAbort('File system scan aborted.')

    return self._NormalizedVolumeIdentifiers(
        volume_system, volume_identifiers, prefix='p')

  def _GetVSSStoreIdentifiers(self, scan_node):
    """Determines the VSS store identifiers.

    Args:
      scan_node (dfvfs.SourceScanNode): scan node.

    Returns:
      list[str]: VSS store identifiers.

    Raises:
      SourceScannerError: if the format of or within the source is not
          supported or the scan node is invalid.
      UserAbort: if the user requested to abort.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid scan node.')

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      return []

    # TODO: refactor to use scan options.
    if self._vss_stores:
      if self._vss_stores == 'all':
        vss_stores = range(1, volume_system.number_of_volumes + 1)
      else:
        vss_stores = self._ParseVolumeIdentifiersString(
            self._vss_stores, prefix='vss')

      selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
          volume_system, vss_stores, prefix='vss')

      if not set(selected_volume_identifiers).difference(volume_identifiers):
        return selected_volume_identifiers

    try:
      volume_identifiers = self._PromptUserForVSSStoreIdentifiers(
          volume_system, volume_identifiers)

    except KeyboardInterrupt:
      raise errors.UserAbort('File system scan aborted.')

    return self._NormalizedVolumeIdentifiers(
        volume_system, volume_identifiers, prefix='vss')

  def _NormalizedVolumeIdentifiers(
      self, volume_system, volume_identifiers, prefix='v'):
    """Normalizes volume identifiers.

    Args:
      volume_system (VolumeSystem): volume system.
      volume_identifiers (list[int|str]): allowed volume identifiers, formatted
          as an integer or string with prefix.
      prefix (Optional[str]): volume identifier prefix.

    Returns:
      list[str]: volume identifiers with prefix.

    Raises:
      SourceScannerError: if the volume identifier is not supported or no
          volume could be found that corresponds with the identifier.
    """
    normalized_volume_identifiers = []
    for volume_identifier in volume_identifiers:
      if isinstance(volume_identifier, int):
        volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)

      elif not volume_identifier.startswith(prefix):
        try:
          volume_identifier = int(volume_identifier, 10)
          volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)
        except (TypeError, ValueError):
          pass

      try:
        volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      except KeyError:
        volume = None

      if not volume:
        raise errors.SourceScannerError(
            'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      normalized_volume_identifiers.append(volume_identifier)

    return normalized_volume_identifiers

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
          credential_data = codecs.decode(credential_data, 'hex')
        except TypeError:
          raise errors.BadConfigOption(
              'Unsupported credential data for: {0:s}.'.format(
                  credential_string))

      self._credentials.append((credential_type, credential_data))

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
    self._partitions = getattr(options, 'partitions', None)
    if self._partitions:
      try:
        self._ParseVolumeIdentifiersString(self._partitions, prefix='p')
      except ValueError:
        raise errors.BadConfigOption('Unsupported partitions')

    self._volumes = getattr(options, 'volumes', None)
    if self._volumes:
      try:
        self._ParseVolumeIdentifiersString(self._volumes, prefix='apfs')
      except ValueError:
        raise errors.BadConfigOption('Unsupported volumes')

  def _ParseVolumeIdentifiersString(
      self, volume_identifiers_string, prefix='v'):
    """Parses a user specified volume identifiers string.

    Args:
      volume_identifiers_string (str): user specified volume identifiers. A
          range of volumes can be defined as: "3..5". Multiple volumes can be
          defined as: "1,3,5" (a list of comma separated values). Ranges and
          lists can also be combined as: "1,3..5". The first volume is 1. All
          volumes can be defined as: "all".
      prefix (Optional[str]): volume identifier prefix.

    Returns:
      list[str]: volume identifiers with prefix or the string "all".

    Raises:
      ValueError: if the volume identifiers string is invalid.
    """
    prefix_length = 0
    if prefix:
      prefix_length = len(prefix)

    if not volume_identifiers_string:
      return []

    if volume_identifiers_string == 'all':
      return ['all']

    volume_identifiers = set()
    for identifiers_range in volume_identifiers_string.split(','):
      # Determine if the range is formatted as 1..3 otherwise it indicates
      # a single volume identifier.
      if '..' in identifiers_range:
        first_identifier, last_identifier = identifiers_range.split('..')

        if first_identifier.startswith(prefix):
          first_identifier = first_identifier[prefix_length:]

        if last_identifier.startswith(prefix):
          last_identifier = last_identifier[prefix_length:]

        try:
          first_identifier = int(first_identifier, 10)
          last_identifier = int(last_identifier, 10)
        except ValueError:
          raise ValueError('Invalid volume identifiers range: {0:s}.'.format(
              identifiers_range))

        for volume_identifier in range(first_identifier, last_identifier + 1):
          if volume_identifier not in volume_identifiers:
            volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)
            volume_identifiers.add(volume_identifier)
      else:
        identifier = identifiers_range
        if identifier.startswith(prefix):
          identifier = identifiers_range[prefix_length:]

        try:
          volume_identifier = int(identifier, 10)
        except ValueError:
          raise ValueError('Invalid volume identifier range: {0:s}.'.format(
              identifiers_range))

        volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)
        volume_identifiers.add(volume_identifier)

    # Note that sorted will return a list.
    return sorted(volume_identifiers)

  def _ParseVSSProcessingOptions(self, options):
    """Parses the VSS processing options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    vss_only = False
    vss_stores = None

    self._process_vss = not getattr(options, 'no_vss', False)
    if self._process_vss:
      vss_only = getattr(options, 'vss_only', False)
      vss_stores = getattr(options, 'vss_stores', None)

    if vss_stores:
      try:
        self._ParseVolumeIdentifiersString(vss_stores, prefix='vss')
      except ValueError:
        raise errors.BadConfigOption('Unsupported VSS stores')

    self._vss_only = vss_only
    self._vss_stores = vss_stores

  def _PrintAPFSVolumeIdentifiersOverview(
      self, volume_system, volume_identifiers):
    """Prints an overview of APFS volume identifiers.

    Args:
      volume_system (dfvfs.APFSVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Raises:
      SourceScannerError: if a volume cannot be resolved from the volume
          identifier.
    """
    header = 'The following Apple File System (APFS) volumes were found:\n'
    self._output_writer.Write(header)

    column_names = ['Identifier', 'Name']
    table_view = views.CLITabularTableView(column_names=column_names)

    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.SourceScannerError(
            'Volume missing for identifier: {0:s}.'.format(
                volume_identifier))

      volume_attribute = volume.GetAttribute('name')
      table_view.AddRow([volume.identifier, volume_attribute.value])

    self._output_writer.Write('\n')
    table_view.Write(self._output_writer)
    self._output_writer.Write('\n')

  def _PrintTSKPartitionIdentifiersOverview(
      self, volume_system, volume_identifiers):
    """Prints an overview of TSK partition identifiers.

    Args:
      volume_system (dfvfs.TSKVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Raises:
      SourceScannerError: if a volume cannot be resolved from the volume
          identifier.
    """
    header = 'The following partitions were found:\n'
    self._output_writer.Write(header)

    column_names = ['Identifier', 'Offset (in bytes)', 'Size (in bytes)']
    table_view = views.CLITabularTableView(column_names=column_names)

    for volume_identifier in sorted(volume_identifiers):
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.SourceScannerError(
            'Partition missing for identifier: {0:s}.'.format(
                volume_identifier))

      volume_extent = volume.extents[0]
      volume_offset = '{0:d} (0x{0:08x})'.format(volume_extent.offset)
      volume_size = self._FormatHumanReadableSize(volume_extent.size)

      table_view.AddRow([volume.identifier, volume_offset, volume_size])

    self._output_writer.Write('\n')
    table_view.Write(self._output_writer)
    self._output_writer.Write('\n')

  def _PrintVSSStoreIdentifiersOverview(
      self, volume_system, volume_identifiers):
    """Prints an overview of VSS store identifiers.

    Args:
      volume_system (dfvfs.VShadowVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Raises:
      SourceScannerError: if a volume cannot be resolved from the volume
          identifier.
    """
    header = 'The following Volume Shadow Snapshots (VSS) were found:\n'
    self._output_writer.Write(header)

    column_names = ['Identifier', 'Creation Time']
    table_view = views.CLITabularTableView(column_names=column_names)

    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.SourceScannerError(
            'Volume missing for identifier: {0:s}.'.format(
                volume_identifier))

      volume_attribute = volume.GetAttribute('creation_time')
      filetime = dfdatetime_filetime.Filetime(timestamp=volume_attribute.value)
      creation_time = filetime.CopyToDateTimeString()

      if volume.HasExternalData():
        creation_time = '{0:s}\tWARNING: data stored outside volume'.format(
            creation_time)

      table_view.AddRow([volume.identifier, creation_time])

    self._output_writer.Write('\n')
    table_view.Write(self._output_writer)
    self._output_writer.Write('\n')

  def _PromptUserForAPFSVolumeIdentifiers(
      self, volume_system, volume_identifiers):
    """Prompts the user to provide APFS volume identifiers.

    Args:
      volume_system (dfvfs.APFSVolumeSystem): volume system.
      volume_identifiers (list[str]): volume identifiers including prefix.

    Returns:
      list[str]: selected volume identifiers including prefix or None.
    """
    print_header = True
    while True:
      if print_header:
        self._PrintAPFSVolumeIdentifiersOverview(
            volume_system, volume_identifiers)

        print_header = False

      lines = self._textwrapper.wrap(self._USER_PROMPT_APFS)
      self._output_writer.Write('\n'.join(lines))
      self._output_writer.Write('\n\nVolume identifiers: ')

      try:
        selected_volumes = self._ReadSelectedVolumes(
            volume_system, prefix='apfs')
        if (not selected_volumes or
            not set(selected_volumes).difference(volume_identifiers)):
          break
      except ValueError:
        pass

      self._output_writer.Write('\n')

      lines = self._textwrapper.wrap(
          'Unsupported volume identifier(s), please try again or abort with '
          'Ctrl^C.')
      self._output_writer.Write('\n'.join(lines))
      self._output_writer.Write('\n\n')

    return selected_volumes

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
    if locked_scan_node.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER):
      header = 'Found an APFS encrypted volume.'
    elif locked_scan_node.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_BDE):
      header = 'Found a BitLocker encrypted volume.'
    elif locked_scan_node.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_FVDE):
      header = 'Found a CoreStorage (FVDE) encrypted volume.'
    else:
      header = 'Found an encrypted volume.'

    self._output_writer.Write(header)

    credentials_list = list(credentials.CREDENTIALS)
    credentials_list.append('skip')

    self._output_writer.Write('Supported credentials:\n\n')

    for index, name in enumerate(credentials_list):
      available_credential = '  {0:d}. {1:s}\n'.format(index + 1, name)
      self._output_writer.Write(available_credential)

    self._output_writer.Write('\nNote that you can abort with Ctrl^C.\n\n')

    result = False
    while not result:
      self._output_writer.Write('Select a credential to unlock the volume: ')

      input_line = self._input_reader.Read()
      input_line = input_line.strip()

      if input_line in credentials_list:
        credential_type = input_line
      else:
        try:
          credential_type = int(input_line, 10)
          credential_type = credentials_list[credential_type - 1]
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

      if credential_type == 'key':
        try:
          credential_data = codecs.decode(credential_data, 'hex')
        except TypeError:
          self._output_writer.Write('Unsupported credential data.\n')
          continue

      result = self._source_scanner.Unlock(
          scan_context, locked_scan_node.path_spec, credential_type,
          credential_data)

      if not result:
        self._output_writer.Write('Unable to unlock volume.\n\n')

    return result

  def _PromptUserForPartitionIdentifiers(
      self, volume_system, volume_identifiers):
    """Prompts the user to provide partition identifiers.

    Args:
      volume_system (dfvfs.TSKVolumeSystem): volume system.
      volume_identifiers (list[str]): volume identifiers including prefix.

    Returns:
      list[str]: selected volume identifiers including prefix or None.
    """
    print_header = True
    while True:
      if print_header:
        self._PrintTSKPartitionIdentifiersOverview(
            volume_system, volume_identifiers)

        print_header = False

      lines = self._textwrapper.wrap(self._USER_PROMPT_TSK)
      self._output_writer.Write('\n'.join(lines))
      self._output_writer.Write('\n\nPartition identifiers: ')

      try:
        selected_volumes = self._ReadSelectedVolumes(volume_system, prefix='p')
        if (selected_volumes and
            not set(selected_volumes).difference(volume_identifiers)):
          break
      except ValueError:
        pass

      self._output_writer.Write('\n')

      lines = self._textwrapper.wrap(
          'Unsupported partition identifier(s), please try again or abort with '
          'Ctrl^C.')
      self._output_writer.Write('\n'.join(lines))
      self._output_writer.Write('\n\n')

    return selected_volumes

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
      self, volume_system, volume_identifiers):
    """Prompts the user to provide VSS store identifiers.

    This method first checks for the preferred VSS stores and falls back
    to prompt the user if no usable preferences were specified.

    Args:
      volume_system (dfvfs.VShadowVolumeSystem): volume system.
      volume_identifiers (list[str]): volume identifiers including prefix.

    Returns:
      list[str]: selected volume identifiers including prefix or None.
    """
    print_header = True
    while True:
      if print_header:
        self._PrintVSSStoreIdentifiersOverview(
            volume_system, volume_identifiers)

        print_header = False

      lines = self._textwrapper.wrap(self._USER_PROMPT_VSS)
      self._output_writer.Write('\n'.join(lines))
      self._output_writer.Write('\n\nVSS identifiers: ')

      try:
        selected_volumes = self._ReadSelectedVolumes(
            volume_system, prefix='vss')
        if (not selected_volumes or
            not set(selected_volumes).difference(volume_identifiers)):
          break
      except ValueError:
        pass

      self._output_writer.Write('\n')

      lines = self._textwrapper.wrap(
          'Unsupported VSS identifier(s), please try again or abort with '
          'Ctrl^C.')
      self._output_writer.Write('\n'.join(lines))
      self._output_writer.Write('\n\n')

    return selected_volumes

  def _ReadSelectedVolumes(self, volume_system, prefix='v'):
    """Reads the selected volumes provided by the user.

    Args:
      volume_system (APFSVolumeSystem): volume system.
      prefix (Optional[str]): volume identifier prefix.

    Returns:
      list[str]: selected volume identifiers including prefix.

    Raises:
      KeyboardInterrupt: if the user requested to abort.
      ValueError: if the volume identifiers string could not be parsed.
    """
    volume_identifiers_string = self._input_reader.Read()
    volume_identifiers_string = volume_identifiers_string.strip()

    if not volume_identifiers_string:
      return []

    selected_volumes = self._ParseVolumeIdentifiersString(
        volume_identifiers_string, prefix=prefix)

    if selected_volumes == ['all']:
      return [
          '{0:s}{1:d}'.format(prefix, volume_index)
          for volume_index in range(1, volume_system.number_of_volumes + 1)]

    return selected_volumes

  def _ScanEncryptedVolume(self, scan_context, scan_node):
    """Scans an encrypted volume scan node for volume and file systems.

    Args:
      scan_context (SourceScannerContext): source scanner context.
      scan_node (SourceScanNode): volume scan node.

    Raises:
      SourceScannerError: if the format of or within the source is not
          supported, the scan node is invalid or there are no credentials
          defined for the format.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid or missing scan node.')

    credentials = credentials_manager.CredentialsManager.GetCredentials(
        scan_node.path_spec)
    if not credentials:
      raise errors.SourceScannerError('Missing credentials for scan node.')

    credentials_dict = {
        credential_type: credential_data
        for credential_type, credential_data in self._credentials}

    is_unlocked = False
    for credential_type in credentials.CREDENTIALS:
      credential_data = credentials_dict.get(credential_type, None)
      if not credential_data:
        continue

      is_unlocked = self._source_scanner.Unlock(
          scan_context, scan_node.path_spec, credential_type, credential_data)
      if is_unlocked:
        break

    if not is_unlocked:
      is_unlocked = self._PromptUserForEncryptedVolumeCredential(
          scan_context, scan_node, credentials)

    if is_unlocked:
      self._source_scanner.Scan(
          scan_context, scan_path_spec=scan_node.path_spec)

  def _ScanFileSystem(self, scan_node, base_path_specs):
    """Scans a file system scan node for file systems.

    Args:
      scan_node (SourceScanNode): file system scan node.
      base_path_specs (list[PathSpec]): file system base path specifications.

    Raises:
      SourceScannerError: if the scan node is invalid.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError(
          'Invalid or missing file system scan node.')

    base_path_specs.append(scan_node.path_spec)

  def _ScanVolume(self, scan_context, scan_node, base_path_specs):
    """Scans a volume scan node for volume and file systems.

    Args:
      scan_context (SourceScannerContext): source scanner context.
      scan_node (SourceScanNode): volume scan node.
      base_path_specs (list[PathSpec]): file system base path specifications.

    Raises:
      SourceScannerError: if the format of or within the source
          is not supported or the scan node is invalid.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid or missing scan node.')

    if scan_context.IsLockedScanNode(scan_node.path_spec):
      # The source scanner found a locked volume and we need a credential to
      # unlock it.
      self._ScanEncryptedVolume(scan_context, scan_node)

      if scan_context.IsLockedScanNode(scan_node.path_spec):
        return

    if scan_node.IsVolumeSystemRoot():
      self._ScanVolumeSystemRoot(scan_context, scan_node, base_path_specs)

    elif scan_node.IsFileSystem():
      self._ScanFileSystem(scan_node, base_path_specs)

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
      if self._process_vss:
        # TODO: look into building VSS store on demand.

        # We "optimize" here for user experience, alternatively we could scan
        # for a file system instead of hard coding a TSK child path
        # specification.
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
            parent=scan_node.path_spec)

        base_path_specs.append(path_spec)

    else:
      for sub_scan_node in scan_node.sub_nodes:
        self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

  def _ScanVolumeSystemRoot(self, scan_context, scan_node, base_path_specs):
    """Scans a volume system root scan node for volume and file systems.

    Args:
      scan_context (SourceScannerContext): source scanner context.
      scan_node (SourceScanNode): volume system root scan node.
      base_path_specs (list[PathSpec]): file system base path specifications.

    Raises:
      SourceScannerError: if the scan node is invalid, the scan node type is not
          supported or if a sub scan node cannot be retrieved.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid scan node.')

    if scan_node.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER):
      volume_identifiers = self._GetAPFSVolumeIdentifiers(scan_node)

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
      if self._process_vss:
        volume_identifiers = self._GetVSSStoreIdentifiers(scan_node)
        # Process VSS stores (snapshots) starting with the most recent one.
        volume_identifiers.reverse()
      else:
        volume_identifiers = []

    else:
      raise errors.SourceScannerError(
          'Unsupported volume system type: {0:s}.'.format(
              scan_node.type_indicator))

    for volume_identifier in volume_identifiers:
      location = '/{0:s}'.format(volume_identifier)
      sub_scan_node = scan_node.GetSubNodeByLocation(location)
      if not sub_scan_node:
        raise errors.SourceScannerError(
            'Scan node missing for volume identifier: {0:s}.'.format(
                volume_identifier))

      self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

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
        '--partitions', '--partition', dest='partitions', action='store',
        type=str, default=None, help=(
            'Define partitions to be processed. A range of '
            'partitions can be defined as: "3..5". Multiple partitions can '
            'be defined as: "1,3,5" (a list of comma separated values). '
            'Ranges and lists can also be combined as: "1,3..5". The first '
            'partition is 1. All partitions can be specified with: "all".'))

    argument_group.add_argument(
        '--volumes', '--volume', dest='volumes', action='store', type=str,
        default=None, help=(
            'Define volumes to be processed. A range of volumes can be defined '
            'as: "3..5". Multiple volumes can be defined as: "1,3,5" (a list '
            'of comma separated values). Ranges and lists can also be combined '
            'as: "1,3..5". The first volume is 1. All volumes can be specified '
            'with: "all".'))

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
    except (ValueError, dfvfs_errors.BackEndError) as exception:
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

    base_path_specs = []
    if scan_node.type_indicator != (
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
      self._ScanVolume(scan_context, scan_node, base_path_specs)

    else:
      # Determine which partition needs to be processed.
      partition_identifiers = self._GetTSKPartitionIdentifiers(scan_node)
      if not partition_identifiers:
        raise errors.SourceScannerError('No partitions found.')

      for partition_identifier in partition_identifiers:
        location = '/{0:s}'.format(partition_identifier)
        sub_scan_node = scan_node.GetSubNodeByLocation(location)
        self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

    if not base_path_specs:
      raise errors.SourceScannerError(
          'No supported file system found in source.')

    self._source_path_specs = base_path_specs

    return scan_context
