# -*- coding: utf-8 -*-
"""The storage media CLI tool."""

import codecs
import getpass
import os

from dfvfs.analyzer import analyzer as dfvfs_analyzer
from dfvfs.analyzer import fvde_analyzer_helper
from dfvfs.credentials import manager as credentials_manager
from dfvfs.helpers import command_line as dfvfs_command_line
from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.volume import apfs_volume_system
from dfvfs.volume import gpt_volume_system
from dfvfs.volume import lvm_volume_system
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import tools
from plaso.engine import configurations
from plaso.lib import errors


try:
  # Disable experimental FVDE support.
  dfvfs_analyzer.Analyzer.DeregisterHelper(
      fvde_analyzer_helper.FVDEAnalyzerHelper())
except KeyError:
  pass


class StorageMediaToolMediator(dfvfs_command_line.CLIVolumeScannerMediator):
  """Mediator between the storage media tool and user input."""

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
    super(StorageMediaToolMediator, self)._PrintAPFSVolumeIdentifiersOverview(
        volume_system, volume_identifiers)
    self._output_writer.Write('\n')

  def _PrintLVMVolumeIdentifiersOverview(
      self, volume_system, volume_identifiers):
    """Prints an overview of LVM volume identifiers.

    Args:
      volume_system (dfvfs.LVMVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Raises:
      SourceScannerError: if a volume cannot be resolved from the volume
          identifier.
    """
    super(StorageMediaToolMediator, self)._PrintLVMVolumeIdentifiersOverview(
        volume_system, volume_identifiers)
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
    super(StorageMediaToolMediator, self)._PrintPartitionIdentifiersOverview(
        volume_system, volume_identifiers)
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
    super(StorageMediaToolMediator, self)._PrintVSSStoreIdentifiersOverview(
        volume_system, volume_identifiers)
    self._output_writer.Write('\n')

  # pylint: disable=arguments-differ
  # TODO: replace this method by the one defined by CLIVolumeScannerMediator
  def ParseVolumeIdentifiersString(
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
    return self._ParseVolumeIdentifiersString(
        volume_identifiers_string, prefix=prefix)

  def PromptUserForEncryptedVolumeCredential(
      self, source_scanner_object, scan_context, locked_scan_node, credentials):
    """Prompts the user to provide a credential for an encrypted volume.

    Args:
      source_scanner_object (SourceScanner): source scanner.
      scan_context (dfvfs.SourceScannerContext): source scanner context.
      locked_scan_node (dfvfs.SourceScanNode): locked scan node.
      credentials (dfvfs.Credentials): credentials supported by the locked
          scan node.

    Returns:
      tuple: contains:

          bool: True if the volume was unlocked.
          credential_identifier (str): credential identifier used to unlock
              the scan node.
          credential_data (bytes): credential data used to unlock the scan node.
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

    credentials_list = sorted(credentials.CREDENTIALS)
    credentials_list.append('skip')

    self._output_writer.Write('Supported credentials:\n\n')

    for index, name in enumerate(credentials_list):
      available_credential = '  {0:d}. {1:s}\n'.format(index + 1, name)
      self._output_writer.Write(available_credential)

    self._output_writer.Write('\nNote that you can abort with Ctrl^C.\n\n')

    is_unlocked = False
    credential_type = None
    credential_data = None
    while not is_unlocked:
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

      credential_data = getpass.getpass('Enter credential data: ')
      self._output_writer.Write('\n')

      if credential_type == 'key':
        try:
          credential_data = codecs.decode(credential_data, 'hex')
        except TypeError:
          self._output_writer.Write('Unsupported credential data.\n')
          continue

      is_unlocked = source_scanner_object.Unlock(
          scan_context, locked_scan_node.path_spec, credential_type,
          credential_data)

      if is_unlocked:
        self._output_writer.Write('Volume unlocked.\n\n')
        break

      self._output_writer.Write('Unable to unlock volume.\n\n')

    return is_unlocked, credential_type, credential_data

  def PromptUserForVSSCurrentVolume(self):
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


class StorageMediaTool(tools.CLITool):
  """CLI tool that supports a storage media device or image as input."""

  # TODO: remove this redirect.
  _SOURCE_OPTION = 'source'

  _BINARY_DATA_CREDENTIAL_TYPES = ['key_data']

  _SUPPORTED_CREDENTIAL_TYPES = [
      'key_data', 'password', 'recovery_password', 'startup_key']

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes a CLI tool that supports storage media as input.

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
    self._mediator = StorageMediaToolMediator(
        input_reader=input_reader, output_writer=output_writer)
    self._partitions = None
    self._process_vss = False
    self._source_scanner = source_scanner.SourceScanner()
    self._source_path = None
    self._source_path_specs = []
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

  def _GetAPFSVolumeIdentifiers(self, scan_node):
    """Determines the APFS volume identifiers.

    Args:
      scan_node (dfvfs.SourceScanNode): scan node.

    Returns:
      list[str]: APFS volume identifiers.

    Raises:
      SourceScannerError: if the scan node is invalid or more than 1 volume
          was found but no volumes were specified.
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
        volumes = volume_system.volume_identifiers
      else:
        volumes = self._mediator.ParseVolumeIdentifiersString(
            self._volumes, prefix='apfs')

      selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
          volume_system, volumes, prefix='apfs')

      if not set(selected_volume_identifiers).difference(volume_identifiers):
        return selected_volume_identifiers

    if len(volume_identifiers) > 1:
      if self._unattended_mode:
        raise errors.SourceScannerError(
            'More than 1 volume found but no volumes specified.')

      try:
        volume_identifiers = self._mediator.GetAPFSVolumeIdentifiers(
            volume_system, volume_identifiers)
      except KeyboardInterrupt:
        raise errors.UserAbort('File system scan aborted.')

    return self._NormalizedVolumeIdentifiers(
        volume_system, volume_identifiers, prefix='apfs')

  def _GetLVMVolumeIdentifiers(self, scan_node):
    """Determines the LVM volume identifiers.

    Args:
      scan_node (dfvfs.SourceScanNode): scan node.

    Returns:
      list[str]: LVM volume identifiers.

    Raises:
      SourceScannerError: if the scan node is invalid or more than 1 volume
          was found but no volumes were specified.
      UserAbort: if the user requested to abort.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid scan node.')

    volume_system = lvm_volume_system.LVMVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      return []

    # TODO: refactor self._volumes to use scan options.
    if self._volumes:
      if self._volumes == 'all':
        volumes = volume_system.volume_identifiers
      else:
        volumes = self._mediator.ParseVolumeIdentifiersString(
            self._volumes, prefix='lvm')

      selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
          volume_system, volumes, prefix='lvm')

      if not set(selected_volume_identifiers).difference(volume_identifiers):
        return selected_volume_identifiers

    if len(volume_identifiers) > 1:
      if self._unattended_mode:
        raise errors.SourceScannerError(
            'More than 1 volume found but no volumes specified.')

      try:
        volume_identifiers = self._mediator.GetLVMVolumeIdentifiers(
            volume_system, volume_identifiers)
      except KeyboardInterrupt:
        raise errors.UserAbort('File system scan aborted.')

    return self._NormalizedVolumeIdentifiers(
        volume_system, volume_identifiers, prefix='lvm')

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
      SourceScannerError: if the scan node is invalid or more than 1 volume
          was found but no volumes were specified.
      UserAbort: if the user requested to abort.
    """
    if not scan_node or not scan_node.path_spec:
      raise errors.SourceScannerError('Invalid scan node.')

    if scan_node.path_spec.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_GPT):
      volume_system = gpt_volume_system.GPTVolumeSystem()
    else:
      volume_system = tsk_volume_system.TSKVolumeSystem()

    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)
    if not volume_identifiers:
      return []

    # TODO: refactor self._partitions to use scan options.
    if self._partitions:
      if self._partitions == 'all':
        partitions = volume_system.volume_identifiers
      else:
        partitions = self._mediator.ParseVolumeIdentifiersString(
            self._partitions, prefix='p')

      selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
          volume_system, partitions, prefix='p')

      if not set(selected_volume_identifiers).difference(volume_identifiers):
        return selected_volume_identifiers

    if len(volume_identifiers) > 1:
      if self._unattended_mode:
        raise errors.SourceScannerError(
            'More than 1 partition found but no partitions specified.')

      try:
        volume_identifiers = self._mediator.GetPartitionIdentifiers(
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
      SourceScannerError: if the scan node is invalid.
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
        vss_stores = volume_system.volume_identifiers
      else:
        vss_stores = self._mediator.ParseVolumeIdentifiersString(
            self._vss_stores, prefix='vss')

      selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
          volume_system, vss_stores, prefix='vss')

      if not set(selected_volume_identifiers).difference(volume_identifiers):
        return selected_volume_identifiers

    if self._unattended_mode:
      return []

    try:
      volume_identifiers = self._mediator.GetVSSStoreIdentifiers(
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
        self._mediator.ParseVolumeIdentifiersString(
            self._partitions, prefix='p')
      except ValueError:
        raise errors.BadConfigOption('Unsupported partitions')

    self._volumes = getattr(options, 'volumes', None)
    if self._volumes:
      try:
        self._mediator.ParseVolumeIdentifiersString(
            self._volumes, prefix='apfs')
      except ValueError:
        raise errors.BadConfigOption('Unsupported volumes')

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
        self._mediator.ParseVolumeIdentifiersString(vss_stores, prefix='vss')
      except ValueError:
        raise errors.BadConfigOption('Unsupported VSS stores')

    self._vss_only = vss_only
    self._vss_stores = vss_stores

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

    credentials_dict = dict(self._credentials)

    is_unlocked = False
    for credential_type in sorted(credentials.CREDENTIALS):
      credential_data = credentials_dict.get(credential_type, None)
      if not credential_data:
        continue

      is_unlocked = self._source_scanner.Unlock(
          scan_context, scan_node.path_spec, credential_type, credential_data)
      if is_unlocked:
        self._AddCredentialConfiguration(
            scan_node.path_spec, credential_type, credential_data)
        break

    if not is_unlocked and not self._unattended_mode:
      is_unlocked, credential_type, credential_data = (
          self._mediator.PromptUserForEncryptedVolumeCredential(
              self._source_scanner, scan_context, scan_node, credentials))

    if is_unlocked:
      self._AddCredentialConfiguration(
          scan_node.path_spec, credential_type, credential_data)
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

    if self._vss_only:
      if scan_node.parent_node.sub_nodes[0].type_indicator == (
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW):
        return

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
        # for a file system instead of hard coding a child path specification.
        if dfvfs_definitions.PREFERRED_NTFS_BACK_END == (
            dfvfs_definitions.TYPE_INDICATOR_TSK):
          location = '/'
        else:
          location = '\\'

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.PREFERRED_NTFS_BACK_END, location=location,
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

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_LVM:
      volume_identifiers = self._GetLVMVolumeIdentifiers(scan_node)

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
      if not self._process_vss:
        volume_identifiers = []
      else:
        volume_identifiers = self._GetVSSStoreIdentifiers(scan_node)
        # Process VSS stores (snapshots) starting with the most recent one.
        volume_identifiers.reverse()

        if (not self._vss_only and not self._unattended_mode and
            volume_identifiers):
          self._vss_only = not self._mediator.PromptUserForVSSCurrentVolume()

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
    if scan_node.type_indicator not in (
        dfvfs_definitions.TYPE_INDICATOR_GPT,
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
