# -*- coding: utf-8 -*-
"""The extraction CLI tool."""

from __future__ import unicode_literals

from dfvfs.resolver import context as dfvfs_context

# The following import makes sure the analyzers are registered.
from plaso import analyzers  # pylint: disable=unused-import

# The following import makes sure the parsers are registered.
from plaso import parsers  # pylint: disable=unused-import

from plaso.cli import logger
from plaso.cli import storage_media_tool
from plaso.cli import tool_options
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import configurations
from plaso.engine import engine
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import manager as parsers_manager


class ExtractionTool(
    storage_media_tool.StorageMediaTool,
    tool_options.HashersOptions,
    tool_options.ParsersOptions,
    tool_options.ProfilingOptions,
    tool_options.StorageFileOptions):
  """Extraction CLI tool."""

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  _BYTES_IN_A_MIB = 1024 * 1024

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
    self._artifacts_registry = None
    self._buffer_size = 0
    self._mount_path = None
    self._operating_system = None
    self._preferred_year = None
    self._process_archives = False
    self._process_compressed_streams = True
    self._process_memory_limit = None
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._resolver_context = dfvfs_context.Context()
    self._single_process_mode = False
    self._storage_file_path = None
    self._storage_format = definitions.STORAGE_FORMAT_SQLITE
    self._temporary_directory = None
    self._text_prepend = None
    self._use_zeromq = True
    self._yara_rules_string = None

  def _CreateProcessingConfiguration(self, knowledge_base):
    """Creates a processing configuration.

    Args:
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for parsing.

    Returns:
      ProcessingConfiguration: processing configuration.
    """
    # TODO: pass preferred_encoding.
    configuration = configurations.ProcessingConfiguration()
    configuration.artifact_filters = self._artifact_filters
    configuration.credentials = self._credential_configurations
    configuration.debug_output = self._debug_mode
    configuration.event_extraction.text_prepend = self._text_prepend
    configuration.extraction.hasher_file_size_limit = (
        self._hasher_file_size_limit)
    configuration.extraction.hasher_names_string = self._hasher_names_string
    configuration.extraction.process_archives = self._process_archives
    configuration.extraction.process_compressed_streams = (
        self._process_compressed_streams)
    configuration.extraction.yara_rules_string = self._yara_rules_string
    configuration.filter_file = self._filter_file
    configuration.input_source.mount_path = self._mount_path
    configuration.log_filename = self._log_file
    configuration.parser_filter_expression = self._parser_filter_expression
    configuration.preferred_year = self._preferred_year
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.sample_rate = self._profiling_sample_rate
    configuration.profiling.profilers = self._profilers
    configuration.temporary_directory = self._temporary_directory

    if not configuration.parser_filter_expression:
      operating_system = knowledge_base.GetValue('operating_system')
      operating_system_product = knowledge_base.GetValue(
          'operating_system_product')
      operating_system_version = knowledge_base.GetValue(
          'operating_system_version')
      parser_filter_expression = (
          parsers_manager.ParsersManager.GetPresetForOperatingSystem(
              operating_system, operating_system_product,
              operating_system_version))

      if parser_filter_expression:
        logger.info('Parser filter expression changed to: {0:s}'.format(
            parser_filter_expression))

      configuration.parser_filter_expression = parser_filter_expression

    return configuration

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
            'Invalid buffer size: {0:s}.'.format(self._buffer_size))

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
        'process_resources', 'temporary_directory', 'workers', 'zeromq']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

  def _PreprocessSources(self, extraction_engine):
    """Preprocesses the sources.

    Args:
      extraction_engine (BaseEngine): extraction engine to preprocess
          the sources.
    """
    logger.debug('Starting preprocessing.')

    try:
      artifacts_registry = engine.BaseEngine.BuildArtifactsRegistry(
          self._artifact_definitions_path, self._custom_artifacts_path)
      extraction_engine.PreprocessSources(
          artifacts_registry, self._source_path_specs,
          resolver_context=self._resolver_context)

    except IOError as exception:
      logger.error('Unable to preprocess with error: {0!s}'.format(exception))

    logger.debug('Preprocessing done.')

  def _SetExtractionParsersAndPlugins(self, configuration, session):
    """Sets the parsers and plugins before extraction.

    Args:
      configuration (ProcessingConfiguration): processing configuration.
      session (Session): session.
    """
    names_generator = parsers_manager.ParsersManager.GetParserAndPluginNames(
        parser_filter_expression=configuration.parser_filter_expression)

    session.enabled_parser_names = list(names_generator)
    session.parser_filter_expression = configuration.parser_filter_expression

  def _SetExtractionPreferredTimeZone(self, knowledge_base):
    """Sets the preferred time zone before extraction.

    Args:
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for parsing.
    """
    # Note session.preferred_time_zone will default to UTC but
    # self._preferred_time_zone is None when not set.
    if self._preferred_time_zone:
      try:
        knowledge_base.SetTimeZone(self._preferred_time_zone)
      except ValueError:
        # pylint: disable=protected-access
        logger.warning(
            'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
                self._preferred_time_zone, knowledge_base._time_zone.zone))

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

    argument_helper_names = ['temporary_directory', 'workers', 'zeromq']
    if self._CanEnforceProcessMemoryLimit():
      argument_helper_names.append('process_resources')
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=argument_helper_names)
