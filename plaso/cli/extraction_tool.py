# -*- coding: utf-8 -*-
"""Shared functionality for an extraction CLI tool."""

import datetime
import os
import time

import pytz

from dfvfs.analyzer import analyzer as dfvfs_analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context as dfvfs_context

# The following import makes sure the analyzers are registered.
from plaso import analyzers  # pylint: disable=unused-import

# The following import makes sure the parsers are registered.
from plaso import parsers  # pylint: disable=unused-import

from plaso.cli import logger
from plaso.cli import status_view
from plaso.cli import storage_media_tool
from plaso.cli import tool_options
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.containers import artifacts
from plaso.engine import configurations
from plaso.engine import engine
from plaso.single_process import extraction_engine as single_extraction_engine
from plaso.filters import parser_filter
from plaso.helpers import language_tags
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_process import extraction_engine as multi_extraction_engine
from plaso.parsers import manager as parsers_manager
from plaso.parsers import presets as parsers_presets
from plaso.storage import factory as storage_factory


class ExtractionTool(
    storage_media_tool.StorageMediaTool,
    tool_options.HashersOptions,
    tool_options.ProfilingOptions,
    tool_options.StorageFileOptions):
  """Extraction CLI tool.

  Attributes:
    list_language_tags (bool): True if the language tags should be listed.
    list_time_zones (bool): True if the time zones should be listed.
  """

  _BYTES_IN_A_MIB = 1024 * 1024

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  _PRESETS_FILE_NAME = 'presets.yaml'

  _SOURCE_TYPES_TO_PREPROCESS = frozenset([
      dfvfs_definitions.SOURCE_TYPE_DIRECTORY,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE])

  _SUPPORTED_ARCHIVE_TYPES = {
      'iso9660': 'ISO-9660 disk image (.iso) file',
      'modi': 'MacOS disk image (.dmg) file',
      'tar': 'tape archive (.tar) file',
      'vhdi': 'Virtual Hard Disk image (.vhd, .vhdx) file',
      'zip': 'ZIP archive (.zip) file'}

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes an CLI tool.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(ExtractionTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._archive_types_string = 'none'
    self._artifacts_registry = None
    self._buffer_size = 0
    self._command_line_arguments = None
    self._enable_sigsegv_handler = False
    self._expanded_parser_filter_expression = None
    self._extract_winevt_resources = True
    self._number_of_extraction_workers = 0
    self._parser_filter_expression = None
    self._preferred_codepage = None
    self._preferred_language = None
    self._preferred_time_zone = None
    self._preferred_year = None
    self._presets_file = None
    self._presets_manager = parsers_presets.ParserPresetsManager()
    # Kept for backwards compatibility.
    self._process_archives = False
    self._process_compressed_streams = True
    self._process_memory_limit = None
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._resolver_context = dfvfs_context.Context()
    self._single_process_mode = False
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._status_view_file = 'status.info'
    self._status_view_interval = 0.5
    self._status_view_mode = status_view.StatusView.MODE_WINDOW
    self._storage_file_path = None
    self._storage_format = definitions.STORAGE_FORMAT_SQLITE
    self._task_storage_format = definitions.STORAGE_FORMAT_SQLITE
    self._temporary_directory = None
    self._worker_memory_limit = None
    self._worker_timeout = None
    self._yara_rules_string = None

    self.list_language_tags = False
    self.list_time_zones = False

  def _CheckStorageFile(self, storage_file_path, warn_about_existing=False):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path (str): path of the storage file.
      warn_about_existing (bool): True if the user should be warned about
          the storage file already existing.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))

      if warn_about_existing:
        logger.warning('Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          'Unable to write to storage file: {0:s}'.format(storage_file_path))

  def _CreateExtractionEngine(self, single_process_mode):
    """Creates an extraction engine.

    Args:
      single_process_mode (bool): True if the engine should use single process
          mode.

    Returns:
      BaseEngine: extraction engine.
    """
    status_update_callback = (
        self._status_view.GetExtractionStatusUpdateCallback())

    if single_process_mode:
      extraction_engine = single_extraction_engine.SingleProcessEngine(
          status_update_callback=status_update_callback)
    else:
      extraction_engine = multi_extraction_engine.ExtractionMultiProcessEngine(
          number_of_worker_processes=self._number_of_extraction_workers,
          status_update_callback=status_update_callback,
          worker_memory_limit=self._worker_memory_limit,
          worker_timeout=self._worker_timeout)

    extraction_engine.SetStatusUpdateInterval(self._status_view_interval)

    return extraction_engine

  def _CreateExtractionProcessingConfiguration(self):
    """Creates an extraction processing configuration.

    Returns:
      ProcessingConfiguration: extraction processing configuration.
    """
    configuration = configurations.ProcessingConfiguration()
    configuration.artifact_definitions_path = self._artifact_definitions_path
    configuration.custom_artifacts_path = self._custom_artifacts_path
    configuration.data_location = self._data_location
    configuration.extraction.archive_types_string = self._archive_types_string
    configuration.artifact_filters = self._artifact_filters
    configuration.credentials = self._credential_configurations
    configuration.debug_output = self._debug_mode
    configuration.extraction.hasher_file_size_limit = (
        self._hasher_file_size_limit)
    configuration.extraction.extract_winevt_resources = (
        self._extract_winevt_resources)
    configuration.extraction.hasher_names_string = self._hasher_names_string
    configuration.extraction.process_compressed_streams = (
        self._process_compressed_streams)
    configuration.extraction.yara_rules_string = self._yara_rules_string
    configuration.filter_file = self._filter_file
    configuration.log_filename = self._log_file
    configuration.parser_filter_expression = (
        self._expanded_parser_filter_expression)
    configuration.preferred_codepage = self._preferred_codepage
    configuration.preferred_language = self._preferred_language
    configuration.preferred_time_zone = self._preferred_time_zone
    configuration.preferred_year = self._preferred_year
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.sample_rate = self._profiling_sample_rate
    configuration.profiling.profilers = self._profilers
    configuration.task_storage_format = self._task_storage_format
    configuration.temporary_directory = self._temporary_directory

    return configuration

  def _GenerateStorageFileName(self):
    """Generates a name for the storage file.

    The result use a timestamp and the basename of the source path.

    Returns:
      str: a filename for the storage file in the form <time>-<source>.plaso

    Raises:
      BadConfigOption: raised if the source path is not set.
    """
    if not self._source_path:
      raise errors.BadConfigOption('Please define a source (--source).')

    timestamp = datetime.datetime.now()
    datetime_string = timestamp.strftime('%Y%m%dT%H%M%S')

    source_path = os.path.abspath(self._source_path)

    if source_path.endswith(os.path.sep):
      source_path = os.path.dirname(source_path)

    source_name = os.path.basename(source_path)

    if not source_name or source_name in ('/', '\\'):
      # The user passed the filesystem's root as source
      source_name = 'ROOT'

    return '{0:s}-{1:s}.plaso'.format(datetime_string, source_name)

  def _GetExpandedParserFilterExpression(self, system_configuration):
    """Determines the expanded parser filter expression.

    Args:
      system_configuration (SystemConfigurationArtifact): system configuration.

    Returns:
      str: expanded parser filter expression.

    Raises:
      BadConfigOption: if presets in the parser filter expression could not
          be expanded or if an invalid parser or plugin name is specified.
    """
    parser_filter_expression = self._parser_filter_expression
    if not parser_filter_expression and system_configuration:
      operating_system_artifact = artifacts.OperatingSystemArtifact(
          family=system_configuration.operating_system,
          product=system_configuration.operating_system_product,
          version=system_configuration.operating_system_version)

      preset_definitions = self._presets_manager.GetPresetsByOperatingSystem(
          operating_system_artifact)
      if preset_definitions:
        self._parser_filter_expression = ','.join([
            preset_definition.name
            for preset_definition in preset_definitions])

        logger.debug('Parser filter expression set to preset: {0:s}'.format(
            self._parser_filter_expression))

    parser_filter_helper = parser_filter.ParserFilterExpressionHelper()

    try:
      parser_filter_expression = parser_filter_helper.ExpandPresets(
          self._presets_manager, self._parser_filter_expression)
      logger.debug('Parser filter expression set to: {0:s}'.format(
          parser_filter_expression or 'N/A'))
    except RuntimeError as exception:
      raise errors.BadConfigOption((
          'Unable to expand presets in parser filter expression with '
          'error: {0!s}').format(exception))

    parser_elements, invalid_parser_elements = (
        parsers_manager.ParsersManager.CheckFilterExpression(
            parser_filter_expression))

    if invalid_parser_elements:
      invalid_parser_names_string = ','.join(invalid_parser_elements)
      raise errors.BadConfigOption(
          'Unknown parser or plugin names in element(s): "{0:s}" of '
          'parser filter expression: {1:s}'.format(
              invalid_parser_names_string, parser_filter_expression))

    return ','.join(sorted(parser_elements))

  def _ParseExtractionOptions(self, options):
    """Parses the extraction options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['codepage', 'language'])

    if self._process_archives:
      self._archive_types_string = 'tar,zip'

      self._PrintUserWarning(
          'The --process_archives option is deprecated use --archives=tar,zip '
          'instead.')

    # TODO: add preferred encoding

    self.list_language_tags = self._preferred_language == 'list'

    self._extract_winevt_resources = getattr(
        options, 'extract_winevt_resources', True)

    time_zone_string = self.ParseStringOption(options, 'timezone')
    if isinstance(time_zone_string, str):
      if time_zone_string.lower() == 'list':
        self.list_time_zones = True

      elif time_zone_string:
        try:
          pytz.timezone(time_zone_string)
        except pytz.UnknownTimeZoneError:
          raise errors.BadConfigOption(
              'Unknown time zone: {0:s}'.format(time_zone_string))

        self._preferred_time_zone = time_zone_string

  def _ParsePerformanceOptions(self, options):
    """Parses the performance options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._buffer_size = getattr(options, 'buffer_size', 0)
    if self._buffer_size:
      # TODO: turn this into a generic function that supports more size
      # suffixes both MB and MiB and also that does not allow m as a valid
      # indicator for MiB since m represents milli not Mega.
      try:
        if self._buffer_size[-1].lower() == 'm':
          self._buffer_size = int(self._buffer_size[:-1], 10)
          self._buffer_size *= self._BYTES_IN_A_MIB
        else:
          self._buffer_size = int(self._buffer_size, 10)
      except ValueError:
        raise errors.BadConfigOption(
            'Invalid buffer size: {0!s}.'.format(self._buffer_size))

    self._queue_size = self.ParseNumericOption(options, 'queue_size')

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._single_process_mode = getattr(options, 'single_process', False)

    argument_helper_names = [
        'process_resources', 'temporary_directory', 'vfs_backend', 'workers',
        'zeromq']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    if self._vfs_back_end == 'fsext':
      dfvfs_definitions.PREFERRED_EXT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_EXT)

    elif self._vfs_back_end == 'fsfat':
      dfvfs_definitions.PREFERRED_FAT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_FAT)

    elif self._vfs_back_end == 'fshfs':
      dfvfs_definitions.PREFERRED_HFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_HFS)

    elif self._vfs_back_end == 'fsntfs':
      dfvfs_definitions.PREFERRED_NTFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_NTFS)

    elif self._vfs_back_end == 'tsk':
      dfvfs_definitions.PREFERRED_EXT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)
      dfvfs_definitions.PREFERRED_FAT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)
      dfvfs_definitions.PREFERRED_GPT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION)
      dfvfs_definitions.PREFERRED_HFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)
      dfvfs_definitions.PREFERRED_NTFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)

    elif self._vfs_back_end == 'vsgpt':
      dfvfs_definitions.PREFERRED_GPT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_GPT)

  def _ProcessSource(self, session, storage_writer):
    """Processes the source and extract events.

    Args:
      session (Session): session in which the source is processed.
      storage_writer (StorageWriter): storage writer to store extracted events.

    Returns:
      ProcessingStatus: processing status.

    Raises:
      BadConfigOption: if an invalid collection filter was specified.
    """
    single_process_mode = self._single_process_mode
    if self._source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      single_process_mode = True

    extraction_engine = self._CreateExtractionEngine(single_process_mode)

    extraction_engine.BuildArtifactsRegistry(
        self._artifact_definitions_path, self._custom_artifacts_path)

    source_configuration = artifacts.SourceConfigurationArtifact(
        path=self._source_path, source_type=self._source_type)

    # TODO: check if the source was processed previously.
    # TODO: add check for modification time of source.

    # If the source is a directory or a storage media image run pre-processing.

    system_configurations = []
    if self._source_type in self._SOURCE_TYPES_TO_PREPROCESS:
      try:
        logger.debug('Starting preprocessing.')

        system_configurations = extraction_engine.PreprocessSource(
            self._file_system_path_specs, storage_writer,
            resolver_context=self._resolver_context)

        logger.debug('Preprocessing done.')

      except IOError as exception:
        system_configurations = []

        logger.error('Unable to preprocess with error: {0!s}'.format(exception))

      # TODO: check if the source was processed previously and if system
      # configuration differs.

    system_configuration = None
    if system_configurations:
      system_configuration = system_configurations[0]

    # TODO: add support for more than 1 system configuration.
    self._expanded_parser_filter_expression = (
        self._GetExpandedParserFilterExpression(system_configuration))

    enabled_parser_names = self._expanded_parser_filter_expression.split(',')

    number_of_enabled_parsers = len(enabled_parser_names)

    force_parser = False
    if (self._source_type == dfvfs_definitions.SOURCE_TYPE_FILE and
        number_of_enabled_parsers == 1):
      force_parser = True

      self._extract_winevt_resources = False

    elif ('winevt' not in enabled_parser_names and
          'winevtx' not in enabled_parser_names):
      self._extract_winevt_resources = False

    elif (self._extract_winevt_resources and
          'pe' not in enabled_parser_names):
      logger.warning(
          'A Windows EventLog parser is enabled in combination with '
          'extraction of Windows EventLog resources, but the Portable '
          'Executable (PE) parser is disabled. Therefore Windows EventLog '
          'resources cannot be extracted.')

      self._extract_winevt_resources = False

    processing_configuration = (
        self._CreateExtractionProcessingConfiguration())
    processing_configuration.force_parser = force_parser

    environment_variables = (
        extraction_engine.knowledge_base.GetEnvironmentVariables())
    user_accounts = list(storage_writer.GetAttributeContainers('user_account'))

    try:
      extraction_engine.BuildCollectionFilters(
          environment_variables, user_accounts,
          artifact_filter_names=self._artifact_filters,
          filter_file_path=self._filter_file)
    except errors.InvalidFilter as exception:
      raise errors.BadConfigOption(
          'Unable to build collection filters with error: {0!s}'.format(
              exception))

    session.artifact_filters = self._artifact_filters
    session.command_line_arguments = self._command_line_arguments
    session.debug_mode = self._debug_mode
    session.enabled_parser_names = enabled_parser_names
    session.extract_winevt_resources = self._extract_winevt_resources
    session.filter_file_path = self._filter_file
    session.parser_filter_expression = self._parser_filter_expression
    session.preferred_codepage = self._preferred_codepage
    session.preferred_encoding = self.preferred_encoding
    session.preferred_language = self._preferred_language or 'en-US'
    session.preferred_time_zone = self._preferred_time_zone
    session.preferred_year = self._preferred_year

    storage_writer.AddAttributeContainer(session)

    processing_status = None

    try:
      storage_writer.AddAttributeContainer(source_configuration)

      for system_configuration in system_configurations:
        storage_writer.AddAttributeContainer(system_configuration)

      if single_process_mode:
        logger.debug('Starting extraction in single process mode.')

        processing_status = extraction_engine.ProcessSource(
            storage_writer, self._resolver_context, processing_configuration,
            system_configurations, self._file_system_path_specs)

      else:
        logger.debug('Starting extraction in multi process mode.')

        # The method is named ProcessSourceMulti because pylint 2.6.0 and
        # later gets confused about keyword arguments when ProcessSource
        # is used.
        processing_status = extraction_engine.ProcessSourceMulti(
            storage_writer, session.identifier, processing_configuration,
            system_configurations, self._file_system_path_specs,
            enable_sigsegv_handler=self._enable_sigsegv_handler,
            storage_file_path=self._storage_file_path)

    finally:
      session.aborted = getattr(processing_status, 'aborted', True)
      session.completion_time = int(time.time() * 1000000)
      storage_writer.UpdateAttributeContainer(session)

    return processing_status

  def _ReadParserPresetsFromFile(self):
    """Reads the parser presets from the presets.yaml file.

    Raises:
      BadConfigOption: if the parser presets file cannot be read.
    """
    self._presets_file = os.path.join(
        self._data_location, self._PRESETS_FILE_NAME)
    if not os.path.isfile(self._presets_file):
      raise errors.BadConfigOption(
          'No such parser presets file: {0:s}.'.format(self._presets_file))

    try:
      self._presets_manager.ReadFromFile(self._presets_file)
    except errors.MalformedPresetError as exception:
      raise errors.BadConfigOption(
          'Unable to read parser presets from file with error: {0!s}'.format(
              exception))

  def _ScanSourceForArchive(self, path_spec):
    """Determines if a path specification references an archive file.

    Args:
      path_spec (dfvfs.PathSpec): path specification of the data stream.

    Returns:
      dfvfs.PathSpec: path specification of the archive file or None if not
          an archive file.
    """
    try:
      type_indicators = (
          dfvfs_analyzer.Analyzer.GetCompressedStreamTypeIndicators(
              path_spec, resolver_context=self._resolver_context))
    except IOError:
      type_indicators = []

    if len(type_indicators) > 1:
      return False

    if type_indicators:
      type_indicator = type_indicators[0]
    else:
      type_indicator = None

    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_BZIP2:
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
          compression_method=dfvfs_definitions.COMPRESSION_METHOD_BZIP2,
          parent=path_spec)

    elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP:
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)

    elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_XZ:
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
          compression_method=dfvfs_definitions.COMPRESSION_METHOD_XZ,
          parent=path_spec)

    try:
      type_indicators = dfvfs_analyzer.Analyzer.GetArchiveTypeIndicators(
          path_spec, resolver_context=self._resolver_context)
    except IOError:
      return None

    if len(type_indicators) != 1:
      return None

    return path_spec_factory.Factory.NewPathSpec(
        type_indicators[0], location='/', parent=path_spec)

  def AddExtractionOptions(self, argument_group):
    """Adds the extraction options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=['codepage', 'language'])

    # Note defaults here are None so we can determine if an option was set.

    argument_group.add_argument(
        '--no_extract_winevt_resources', '--no-extract-winevt-resources',
        dest='extract_winevt_resources', action='store_false', default=True,
        help=('Do not extract Windows EventLog resources such as event '
              'message template strings. By default Windows EventLog '
              'resources will be extracted when a Windows EventLog parser '
              'is enabled.'))

    # TODO: add preferred encoding

    argument_group.add_argument(
        '-z', '--zone', '--timezone', dest='timezone', action='store',
        metavar='TIME_ZONE', type=str, default=None, help=(
            'preferred time zone of extracted date and time values that are '
            'stored without a time zone indicator. The time zone is determined '
            'based on the source data where possible otherwise it will default '
            'to UTC. Use "list" to see a list of available time zones.'))

  def AddPerformanceOptions(self, argument_group):
    """Adds the performance options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--buffer_size', '--buffer-size', '--bs', dest='buffer_size',
        action='store', default=0, help=(
            'The buffer size for the output (defaults to 196MiB).'))

    argument_group.add_argument(
        '--queue_size', '--queue-size', dest='queue_size', action='store',
        default=0, help=(
            'The maximum number of queued items per worker '
            '(defaults to {0:d})').format(self._DEFAULT_QUEUE_SIZE))

  def AddProcessingOptions(self, argument_group):
    """Adds the processing options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--single_process', '--single-process', dest='single_process',
        action='store_true', default=False, help=(
            'Indicate that the tool should run in a single process.'))

    argument_helper_names = [
        'temporary_directory', 'vfs_backend', 'workers', 'zeromq']
    if self._CanEnforceProcessMemoryLimit():
      argument_helper_names.append('process_resources')
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=argument_helper_names)

  def ExtractEventsFromSources(self):
    """Processes the sources and extracts events.

    Raises:
      BadConfigOption: if the storage file path is invalid, or the storage
          format not supported, or there was a failure to writing to the
          storage.
      IOError: if the extraction engine could not write to the storage.
      OSError: if the extraction engine could not write to the storage.
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    self._CheckStorageFile(self._storage_file_path, warn_about_existing=True)

    try:
      self.ScanSource(self._source_path)
    except dfvfs_errors.UserAbort as exception:
      raise errors.UserAbort(exception)

    if self._source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      archive_path_spec = self._ScanSourceForArchive(
          self._file_system_path_specs[0])
      if archive_path_spec:
        self._file_system_path_specs = [archive_path_spec]
        self._source_type = definitions.SOURCE_TYPE_ARCHIVE

    self._status_view.SetMode(self._status_view_mode)
    self._status_view.SetStatusFile(self._status_view_file)
    self._status_view.SetSourceInformation(
        self._source_path, self._source_type,
        artifact_filters=self._artifact_filters,
        filter_file=self._filter_file)

    self._output_writer.Write('\n')
    self._status_view.PrintExtractionStatusHeader(None)
    self._output_writer.Write('Processing started.\n')

    # TODO: attach processing configuration to session?
    session = engine.BaseEngine.CreateSession()

    storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
        self._storage_format)
    if not storage_writer:
      raise errors.BadConfigOption('Unsupported storage format: {0:s}'.format(
          self._storage_format))

    try:
      storage_writer.Open(path=self._storage_file_path)
    except IOError as exception:
      raise IOError('Unable to open storage with error: {0!s}'.format(
          exception))

    processing_status = None
    number_of_extraction_warnings = 0

    try:
      stored_number_of_extraction_warnings = (
          storage_writer.GetNumberOfAttributeContainers('extraction_warning'))

      try:
        processing_status = self._ProcessSource(session, storage_writer)

      finally:
        number_of_extraction_warnings = (
            storage_writer.GetNumberOfAttributeContainers(
                'extraction_warning') - stored_number_of_extraction_warnings)

    except IOError as exception:
      raise IOError('Unable to write to storage with error: {0!s}'.format(
          exception))

    finally:
      storage_writer.Close()

    self._status_view.PrintExtractionSummary(
        processing_status, number_of_extraction_warnings)

  def ListArchiveTypes(self):
    """Lists information about supported archive types."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Archive and storage media image types')

    for name, description in sorted(self._SUPPORTED_ARCHIVE_TYPES.items()):
      table_view.AddRow([name, description])

    table_view.Write(self._output_writer)

  def ListLanguageTags(self):
    """Lists the language tags."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Language tag', 'Description'],
        title='Language tags')
    for language_tag, description in (
        language_tags.LanguageTagHelper.GetLanguages()):
      table_view.AddRow([language_tag, description])
    table_view.Write(self._output_writer)

  def ListParsersAndPlugins(self):
    """Lists information about the available parsers and plugins."""
    parsers_information = parsers_manager.ParsersManager.GetParsersInformation()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Parsers')

    for name, description in sorted(parsers_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

    parser_names = parsers_manager.ParsersManager.GetNamesOfParsersWithPlugins()
    for parser_name in parser_names:
      plugins_information = (
          parsers_manager.ParsersManager.GetParserPluginsInformation(
              parser_filter_expression=parser_name))

      table_title = 'Parser plugins: {0:s}'.format(parser_name)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, column_names=['Name', 'Description'],
          title=table_title)
      for name, description in sorted(plugins_information):
        table_view.AddRow([name, description])
      table_view.Write(self._output_writer)

    title = 'Parser presets'
    if self._presets_file:
      source_path = os.path.dirname(os.path.dirname(os.path.dirname(
          os.path.abspath(__file__))))

      presets_file = self._presets_file
      if presets_file.startswith(source_path):
        presets_file = presets_file[len(source_path) + 1:]

      title = '{0:s} ({1:s})'.format(title, presets_file)

    presets_information = self._presets_manager.GetPresetsInformation()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Parsers and plugins'],
        title=title)
    for name, description in sorted(presets_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)
