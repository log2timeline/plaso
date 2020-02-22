# -*- coding: utf-8 -*-
"""The extraction CLI tool."""

from __future__ import unicode_literals

import os

from dfvfs.resolver import context as dfvfs_context

# The following import makes sure the analyzers are registered.
from plaso import analyzers  # pylint: disable=unused-import

# The following import makes sure the parsers are registered.
from plaso import parsers  # pylint: disable=unused-import

from plaso.containers import artifacts
from plaso.cli import logger
from plaso.cli import storage_media_tool
from plaso.cli import tool_options
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import configurations
from plaso.engine import engine
from plaso.filters import parser_filter
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import manager as parsers_manager
from plaso.parsers import presets as parsers_presets


class ExtractionTool(
    storage_media_tool.StorageMediaTool,
    tool_options.HashersOptions,
    tool_options.ProfilingOptions,
    tool_options.StorageFileOptions):
  """Extraction CLI tool."""

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  _BYTES_IN_A_MIB = 1024 * 1024

  _PRESETS_FILE_NAME = 'presets.yaml'

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
    self._parser_filter_expression = None
    self._preferred_year = None
    self._presets_file = None
    self._presets_manager = parsers_presets.ParserPresetsManager()
    self._process_archives = False
    self._process_compressed_streams = True
    self._process_memory_limit = None
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._resolver_context = dfvfs_context.Context()
    self._single_process_mode = False
    self._storage_file_path = None
    self._storage_format = definitions.STORAGE_FORMAT_SQLITE
    self._task_storage_format = definitions.STORAGE_FORMAT_SQLITE
    self._temporary_directory = None
    self._text_prepend = None
    self._yara_rules_string = None

  def _CreateProcessingConfiguration(self, knowledge_base):
    """Creates a processing configuration.

    Args:
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for parsing.

    Returns:
      ProcessingConfiguration: processing configuration.

    Raises:
      BadConfigOption: if presets in the parser filter expression could not
          be expanded or if an invalid parser or plugin name is specified.
    """
    parser_filter_expression = self._parser_filter_expression
    if not parser_filter_expression:
      operating_system_family = knowledge_base.GetValue('operating_system')
      operating_system_product = knowledge_base.GetValue(
          'operating_system_product')
      operating_system_version = knowledge_base.GetValue(
          'operating_system_version')

      operating_system_artifact = artifacts.OperatingSystemArtifact(
          family=operating_system_family, product=operating_system_product,
          version=operating_system_version)

      preset_definitions = self._presets_manager.GetPresetsByOperatingSystem(
          operating_system_artifact)

      if preset_definitions:
        preset_names = [
            preset_definition.name for preset_definition in preset_definitions]
        filter_expression = ','.join(preset_names)

        logger.info('Parser filter expression set to: {0:s}'.format(
            filter_expression))
        parser_filter_expression = filter_expression

    parser_filter_helper = parser_filter.ParserFilterExpressionHelper()

    try:
      parser_filter_expression = parser_filter_helper.ExpandPresets(
          self._presets_manager, parser_filter_expression)
    except RuntimeError as exception:
      raise errors.BadConfigOption((
          'Unable to expand presets in parser filter expression with '
          'error: {0!s}').format(exception))

    _, invalid_parser_elements = (
        parsers_manager.ParsersManager.CheckFilterExpression(
            parser_filter_expression))

    if invalid_parser_elements:
      invalid_parser_names_string = ','.join(invalid_parser_elements)
      raise errors.BadConfigOption(
          'Unknown parser or plugin names in element(s): "{0:s}" of '
          'parser filter expression: {1:s}'.format(
              invalid_parser_names_string, parser_filter_expression))

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
    configuration.parser_filter_expression = parser_filter_expression
    configuration.preferred_year = self._preferred_year
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.sample_rate = self._profiling_sample_rate
    configuration.profiling.profilers = self._profilers
    configuration.task_storage_format = self._task_storage_format
    configuration.temporary_directory = self._temporary_directory

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
