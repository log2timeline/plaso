# -*- coding: utf-8 -*-
"""The storage media CLI tool."""

import codecs
import os

from dfvfs.analyzer import analyzer as dfvfs_analyzer
from dfvfs.analyzer import cs_analyzer_helper
from dfvfs.helpers import command_line as dfvfs_command_line
from dfvfs.helpers import volume_scanner as dfvfs_volume_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.volume import apfs_volume_system
from dfvfs.volume import lvm_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import tools
from plaso.engine import configurations
from plaso.lib import errors


try:
  # Disable experimental Core Storage support.
  dfvfs_analyzer.Analyzer.DeregisterHelper(
      cs_analyzer_helper.CSAnalyzerHelper())
except KeyError:
  pass


class StorageMediaToolVolumeScannerOptions(
    dfvfs_volume_scanner.VolumeScannerOptions):
  """Volume scanner options used by the storage media tool.

  Attributes:
    snapshots_only (bool): True if the current volume of a volume with snapshots
        should be ignored.
  """

  def __init__(self):
    """Initializes volume scanner options."""
    super(StorageMediaToolVolumeScannerOptions, self).__init__()
    self.snapshots_only = False


class StorageMediaToolMediator(dfvfs_command_line.CLIVolumeScannerMediator):
  """Mediator between the storage media tool and user input."""

  def _PrintAPFSVolumeIdentifiersOverview(
      self, volume_system, volume_identifiers):
    """Prints an overview of APFS volume identifiers.

    Args:
      volume_system (dfvfs.APFSVolumeSystem): volume system.
      volume_identifiers (list[str]): allowed volume identifiers.

    Raises:
      dfvfs.ScannerError: if a volume cannot be resolved from the volume
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
      dfvfs.ScannerError: if a volume cannot be resolved from the volume
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
      dfvfs.ScannerError: if a volume cannot be resolved from the volume
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
      dfvfs.ScannerError: if a volume cannot be resolved from the volume
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


class StorageMediaToolVolumeScanner(dfvfs_volume_scanner.VolumeScanner):
  """Volume scanner used by the storage media tool."""

  def __init__(self, mediator=None):
    """Initializes a volume scanner.

    Args:
      mediator (Optional[VolumeScannerMediator]): a volume scanner mediator.
    """
    super(StorageMediaToolVolumeScanner, self).__init__(mediator=mediator)
    self._credential_configurations = []
    self._snapshots_only = False

  @property
  def source_type(self):
    """str: type of source."""
    return self._source_type

  def _GetBasePathSpecs(self, scan_context, options):
    """Determines the base path specifications.

    Args:
      scan_context (SourceScannerContext): source scanner context.
      options (VolumeScannerOptions): volume scanner options.

    Returns:
      list[PathSpec]: path specifications.

    Raises:
      dfvfs.ScannerError: if the format of or within the source is not
          supported or no partitions were found.
    """
    # TODO: difference with dfVFS.
    self._snapshots_only = options.snapshots_only

    scan_node = scan_context.GetRootScanNode()

    if scan_context.source_type not in (
        scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE):
      return [scan_node.path_spec]

    # Get the first node where where we need to decide what to process.
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    base_path_specs = []
    if scan_node.type_indicator not in (
        dfvfs_definitions.TYPE_INDICATOR_GPT,
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
      self._ScanVolume(scan_context, scan_node, options, base_path_specs)

    else:
      # Determine which partition needs to be processed.
      partition_identifiers = self._GetPartitionIdentifiers(scan_node, options)
      # TODO: difference with dfVFS.
      if not partition_identifiers:
        raise dfvfs_errors.ScannerError('No partitions found.')

      for partition_identifier in partition_identifiers:
        location = '/{0:s}'.format(partition_identifier)
        sub_scan_node = scan_node.GetSubNodeByLocation(location)
        self._ScanVolume(scan_context, sub_scan_node, options, base_path_specs)

    return base_path_specs

  def _ScanEncryptedVolume(self, scan_context, scan_node, options):
    """Scans an encrypted volume scan node for volume and file systems.

    Args:
      scan_context (SourceScannerContext): source scanner context.
      scan_node (SourceScanNode): volume scan node.
      options (VolumeScannerOptions): volume scanner options.

    Raises:
      dfvfs.ScannerError: if the format of or within the source is not
          supported, the scan node is invalid or there are no credentials
          defined for the format.
    """
    super(StorageMediaToolVolumeScanner, self)._ScanEncryptedVolume(
        scan_context, scan_node, options)

    if not scan_context.IsLockedScanNode(scan_node.path_spec):
      credential_type, credential_data = scan_node.credential
      credential_configuration = configurations.CredentialConfiguration(
          credential_data=credential_data, credential_type=credential_type,
          path_spec=scan_node.path_spec)

      self._credential_configurations.append(credential_configuration)

  def _ScanFileSystem(self, scan_node, base_path_specs):
    """Scans a file system scan node for file systems.

    Args:
      scan_node (SourceScanNode): file system scan node.
      base_path_specs (list[PathSpec]): file system base path specifications.

    Raises:
      dfvfs.ScannerError: if the scan node is invalid.
    """
    if not scan_node or not scan_node.path_spec:
      raise dfvfs_errors.ScannerError(
          'Invalid or missing file system scan node.')

    # TODO: difference with dfVFS for current VSS volume support.
    if self._snapshots_only:
      if scan_node.parent_node.sub_nodes[0].type_indicator == (
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW):
        return

    base_path_specs.append(scan_node.path_spec)

  def _ScanVolumeSystemRoot(
      self, scan_context, scan_node, options, base_path_specs):
    """Scans a volume system root scan node for volume and file systems.

    Args:
      scan_context (SourceScannerContext): source scanner context.
      scan_node (SourceScanNode): volume system root scan node.
      options (VolumeScannerOptions): volume scanner options.
      base_path_specs (list[PathSpec]): file system base path specifications.

    Raises:
      dfvfs.ScannerError: if the scan node is invalid, the scan node type is not
          supported or if a sub scan node cannot be retrieved.
    """
    if not scan_node or not scan_node.path_spec:
      raise dfvfs_errors.ScannerError('Invalid scan node.')

    if scan_node.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER):
      volume_system = apfs_volume_system.APFSVolumeSystem()
      volume_system.Open(scan_node.path_spec)

      volume_identifiers = self._GetVolumeIdentifiers(volume_system, options)

    elif scan_node.type_indicator in (
        dfvfs_definitions.TYPE_INDICATOR_GPT,
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
      volume_identifiers = self._GetPartitionIdentifiers(scan_node, options)

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_LVM:
      volume_system = lvm_volume_system.LVMVolumeSystem()
      volume_system.Open(scan_node.path_spec)

      volume_identifiers = self._GetVolumeIdentifiers(volume_system, options)

    elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
      volume_system = vshadow_volume_system.VShadowVolumeSystem()
      volume_system.Open(scan_node.path_spec)

      volume_identifiers = self._GetVolumeSnapshotIdentifiers(
          volume_system, options)
      # Process VSS stores (snapshots) starting with the most recent one.
      volume_identifiers.reverse()

      # TODO: difference with dfVFS for current VSS volume support.
      if not options.snapshots_only and self._mediator and volume_identifiers:
        snapshots_only = not self._mediator.PromptUserForVSSCurrentVolume()
        options.snapshots_only = snapshots_only
        self._snapshots_only = snapshots_only

    else:
      raise dfvfs_errors.ScannerError(
          'Unsupported volume system type: {0:s}.'.format(
              scan_node.type_indicator))

    for volume_identifier in volume_identifiers:
      location = '/{0:s}'.format(volume_identifier)
      sub_scan_node = scan_node.GetSubNodeByLocation(location)
      if not sub_scan_node:
        raise dfvfs_errors.ScannerError(
            'Scan node missing for volume identifier: {0:s}.'.format(
                volume_identifier))

      self._ScanVolume(scan_context, sub_scan_node, options, base_path_specs)

  def ScanSource(self, source_path, options, base_path_specs):
    """Scans the source path for volume and file systems.

    This function sets the internal source path specification and source
    type values.

    Args:
      source_path (str): path to the source.
      options (VolumeScannerOptions): volume scanner options.
      base_path_specs (list[PathSpec]): file system base path specifications.

    Returns:
      dfvfs.SourceScannerContext: source scanner context.

    Raises:
      dfvfs.ScannerError: if the format of or within the source is
          not supported.
    """
    scan_context = self._ScanSource(source_path)

    self._source_path = source_path
    self._source_type = scan_context.source_type

    scanner_base_path_specs = self._GetBasePathSpecs(scan_context, options)
    base_path_specs.extend(scanner_base_path_specs)

    return scan_context


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
    self._file_system_path_specs = []
    self._filter_file = None
    self._mediator = StorageMediaToolMediator(
        input_reader=input_reader, output_writer=output_writer)
    self._partitions = None
    self._source_path = None
    self._source_type = None
    self._volumes = None
    self._vss_only = False
    self._vss_stores = None

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
    process_vss = not getattr(options, 'no_vss', False)
    vss_only = getattr(options, 'vss_only', False)
    vss_stores = getattr(options, 'vss_stores', None)

    if not process_vss:
      vss_stores = 'none'

      self._PrintUserWarning(
          'The --no_vss option is deprecated use --vss_stores=none instead.')

    if vss_stores and vss_stores != 'none':
      try:
        self._mediator.ParseVolumeIdentifiersString(vss_stores, prefix='vss')
      except ValueError:
        raise errors.BadConfigOption('Unsupported VSS stores')

    self._vss_only = vss_only
    self._vss_stores = vss_stores

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
            'Volume Shadow Snapshots (VSS) are not processed. WARNING: this '
            'option is deprecated use --vss_stores=none instead.'))

    argument_group.add_argument(
        '--vss_only', '--vss-only', dest='vss_only', action='store_true',
        default=False, help=(
            'Do not process the current volume if Volume Shadow Snapshots '
            '(VSS) have been selected.'))

    argument_group.add_argument(
        '--vss_stores', '--vss-stores', dest='vss_stores', action='store',
        type=str, default=None, help=(
            'Define Volume Shadow Snapshots (VSS) (or stores) that need to be '
            'processed. A range of snapshots can be defined as: "3..5". '
            'Multiple snapshots can be defined as: "1,3,5" (a list of comma '
            'separated values). Ranges and lists can also be combined as: '
            '"1,3..5". The first snapshot is 1. All snapshots can be defined '
            'as: "all" and no snapshots as: "none".'))

  def ScanSource(self, source_path):
    """Scans the source path for volume and file systems.

    This function sets the internal source path specification and source
    type values.

    Args:
      source_path (str): path to the source.

    Raises:
      SourceScannerError: if the format of or within the source is
          not supported.
    """
    # Symbolic links are resolved here and not earlier to preserve the user
    # specified source path in storage and reporting.
    if os.path.islink(source_path):
      source_path = os.path.realpath(source_path)

    options = StorageMediaToolVolumeScannerOptions()
    options.credentials = self._credentials
    if self._vss_only:
      options.scan_mode = options.SCAN_MODE_SNAPSHOTS_ONLY
    else:
      options.scan_mode = options.SCAN_MODE_ALL
    options.snapshots_only = self._vss_only

    if self._partitions == 'all':
      options.partitions = ['all']
    else:
      options.partitions = self._partitions

    if not self._vss_stores and self._unattended_mode:
      options.snapshots = ['none']
    elif self._vss_stores == 'all':
      options.snapshots = ['all']
    elif self._vss_stores == 'none':
      options.snapshots = ['none']
    else:
      options.snapshots = self._vss_stores

    if self._volumes == 'all':
      options.volumes = ['all']
    else:
      options.volumes = self._volumes

    if self._unattended_mode:
      mediator = None
    else:
      mediator = self._mediator

    volume_scanner = StorageMediaToolVolumeScanner(mediator=mediator)

    try:
      base_path_specs = volume_scanner.GetBasePathSpecs(
          source_path, options=options)
    except dfvfs_errors.ScannerError as exception:
      raise errors.SourceScannerError(exception)

    if not base_path_specs:
      raise errors.SourceScannerError(
          'No supported file system found in source.')

    # pylint: disable=protected-access
    self._credential_configurations = volume_scanner._credential_configurations
    self._file_system_path_specs = base_path_specs
    self._source_type = volume_scanner.source_type
