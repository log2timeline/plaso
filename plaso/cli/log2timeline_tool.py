# -*- coding: utf-8 -*-
"""The log2timeline CLI tool."""

from __future__ import unicode_literals

import argparse
import logging
import sys
import time
import textwrap

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context as dfvfs_context

import plaso

# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import

# The following import makes sure the output modules are registered.
from plaso import output  # pylint: disable=unused-import

from plaso.cli import extraction_tool
from plaso.cli import logging_filter
from plaso.cli import status_view
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import configurations
from plaso.engine import engine
from plaso.engine import single_process as single_process_engine
from plaso.frontend import utils as frontend_utils
from plaso.analyzers.hashers import manager as hashers_manager
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import task_engine as multi_process_engine
from plaso.parsers import manager as parsers_manager
from plaso.storage import sqlite_file as storage_sqlite_file
from plaso.storage import zip_file as storage_zip_file


class Log2TimelineTool(
    extraction_tool.ExtractionTool,
    tool_options.HashersOptions,
    tool_options.ParsersOptions,
    tool_options.StorageFileOptions):
  """Log2timeline CLI tool.

  Attributes:
    dependencies_check (bool): True if the availability and versions of
        dependencies should be checked.
    list_hashers (bool): True if the hashers should be listed.
    list_output_modules (bool): True if information about the output modules
        should be shown.
    list_parsers_and_plugins (bool): True if the parsers and plugins should
        be listed.
    show_info (bool): True if information about hashers, parsers, plugins,
        etc. should be shown.
  """

  NAME = 'log2timeline'
  DESCRIPTION = textwrap.dedent('\n'.join([
      '',
      ('log2timeline is a command line tool to extract events from '
       'individual '),
      'files, recursing a directory (e.g. mount point) or storage media ',
      'image or device.',
      '',
      'More information can be gathered from here:',
      '    https://github.com/log2timeline/plaso/wiki/Using-log2timeline',
      '']))

  EPILOG = textwrap.dedent('\n'.join([
      '',
      'Example usage:',
      '',
      'Run the tool against a storage media image (full kitchen sink)',
      '    log2timeline.py /cases/mycase/storage.plaso ímynd.dd',
      '',
      'Instead of answering questions, indicate some of the options on the',
      'command line (including data from particular VSS stores).',
      ('    log2timeline.py -o 63 --vss_stores 1,2 /cases/plaso_vss.plaso '
       'image.E01'),
      '',
      'And that is how you build a timeline using log2timeline...',
      '']))

  # The window status-view mode has an annoying flicker on Windows,
  # hence we default to linear status-view mode instead.
  if sys.platform.startswith('win'):
    _DEFAULT_STATUS_VIEW_MODE = status_view.StatusView.MODE_LINEAR
  else:
    _DEFAULT_STATUS_VIEW_MODE = status_view.StatusView.MODE_WINDOW

  _SOURCE_TYPES_TO_PREPROCESS = frozenset([
      dfvfs_definitions.SOURCE_TYPE_DIRECTORY,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE])

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(Log2TimelineTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._command_line_arguments = None
    self._enable_sigsegv_handler = False
    self._number_of_extraction_workers = 0
    self._resolver_context = dfvfs_context.Context()
    self._storage_serializer_format = definitions.SERIALIZER_FORMAT_JSON
    self._source_type = None
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._status_view_mode = self._DEFAULT_STATUS_VIEW_MODE
    self._stdout_output_writer = isinstance(
        self._output_writer, tools.StdoutOutputWriter)
    self._storage_file_path = None
    self._storage_format = definitions.STORAGE_FORMAT_ZIP
    self._temporary_directory = None
    self._text_prepend = None
    self._use_zeromq = True
    self._worker_memory_limit = None
    self._yara_rules_string = None

    self.dependencies_check = True
    self.list_hashers = False
    self.list_output_modules = False
    self.list_parsers_and_plugins = False
    self.show_info = False

  def _CreateProcessingConfiguration(self):
    """Creates a processing configuration.

    Returns:
      ProcessingConfiguration: processing configuration.
    """
    # TODO: pass preferred_encoding.
    configuration = configurations.ProcessingConfiguration()
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
    configuration.parser_filter_expression = self._parser_filter_expression
    configuration.preferred_year = self._preferred_year
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.sample_rate = self._profiling_sample_rate
    configuration.profiling.profilers = self._profilers
    configuration.temporary_directory = self._temporary_directory

    return configuration

  def _GetPluginData(self):
    """Retrieves the version and various plugin information.

    Returns:
      dict[str, list[str]]: available parsers and plugins.
    """
    return_dict = {}

    return_dict['Versions'] = [
        ('plaso engine', plaso.__version__),
        ('python', sys.version)]

    hashers_information = hashers_manager.HashersManager.GetHashersInformation()
    parsers_information = parsers_manager.ParsersManager.GetParsersInformation()
    plugins_information = (
        parsers_manager.ParsersManager.GetParserPluginsInformation())
    presets_information = self._GetParserPresetsInformation()

    return_dict['Hashers'] = hashers_information
    return_dict['Parsers'] = parsers_information
    return_dict['Parser Plugins'] = plugins_information
    return_dict['Parser Presets'] = presets_information

    return return_dict

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._use_zeromq = getattr(options, 'use_zeromq', True)

    self._single_process_mode = getattr(options, 'single_process', False)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['temporary_directory'])

    self._worker_memory_limit = getattr(options, 'worker_memory_limit', None)
    self._number_of_extraction_workers = getattr(options, 'workers', 0)

    # TODO: add code to parse the worker options.

  def AddProcessingOptions(self, argument_group):
    """Adds the processing options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--disable_zeromq', '--disable-zeromq', action='store_false',
        dest='use_zeromq', default=True, help=(
            'Disable queueing using ZeroMQ. A Multiprocessing queue will be '
            'used instead.'))

    argument_group.add_argument(
        '--single_process', '--single-process', dest='single_process',
        action='store_true', default=False, help=(
            'Indicate that the tool should run in a single process.'))

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=['temporary_directory'])

    argument_group.add_argument(
        '--worker-memory-limit', '--worker_memory_limit',
        dest='worker_memory_limit', action='store', type=int,
        metavar='SIZE', help=(
            'Maximum amount of memory a worker process is allowed to consume. '
            '[defaults to 2 GiB]'))

    argument_group.add_argument(
        '--workers', dest='workers', action='store', type=int, default=0,
        help=('The number of worker processes [defaults to available system '
              'CPUs minus one].'))

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_parser, names=['storage_file', 'storage_format'])

    extraction_group = argument_parser.add_argument_group(
        'Extraction Arguments')

    argument_helper_names = [
        'artifact_definitions', 'extraction', 'filter_file', 'hashers',
        'parsers', 'yara_rules']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        extraction_group, names=argument_helper_names)

    self.AddStorageMediaImageOptions(extraction_group)
    self.AddTimeZoneOption(extraction_group)
    self.AddVSSProcessingOptions(extraction_group)
    self.AddCredentialOptions(extraction_group)

    info_group = argument_parser.add_argument_group('Informational Arguments')

    self.AddInformationalOptions(info_group)

    info_group.add_argument(
        '--info', dest='show_info', action='store_true', default=False,
        help='Print out information about supported plugins and parsers.')

    info_group.add_argument(
        '--use_markdown', '--use-markdown', dest='use_markdown',
        action='store_true', default=False, help=(
            'Output lists in Markdown format use in combination with '
            '"--hashers list", "--parsers list" or "--timezone list"'))

    info_group.add_argument(
        '--no_dependencies_check', '--no-dependencies-check',
        dest='dependencies_check', action='store_false', default=True,
        help='Disable the dependencies check.')

    self.AddLogFileOptions(info_group)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        info_group, names=['status_view'])

    output_group = argument_parser.add_argument_group('Output Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_group, names=['text_prepend'])

    processing_group = argument_parser.add_argument_group(
        'Processing Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        processing_group, names=['data_location'])

    self.AddPerformanceOptions(processing_group)
    self.AddProfilingOptions(processing_group)
    self.AddProcessingOptions(processing_group)

    processing_group.add_argument(
        '--sigsegv_handler', '--sigsegv-handler', dest='sigsegv_handler',
        action='store_true', default=False, help=(
            'Enables the SIGSEGV handler. WARNING this functionality is '
            'experimental and will a deadlock worker process if a real '
            'segfault is caught, but not signal SIGSEGV. This functionality '
            'is therefore primarily intended for debugging purposes'))

    argument_parser.add_argument(
        self._SOURCE_OPTION, action='store', metavar='SOURCE', nargs='?',
        default=None, type=str, help=(
            'The path to the source device, file or directory. If the source '
            'is a supported storage media device or image file, archive file '
            'or a directory, the files within are processed recursively.'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    # Properly prepare the attributes according to local encoding.
    if self.preferred_encoding == 'ascii':
      logging.warning(
          'The preferred encoding of your system is ASCII, which is not '
          'optimal for the typically non-ASCII characters that need to be '
          'parsed and processed. The tool will most likely crash and die, '
          'perhaps in a way that may not be recoverable. A five second delay '
          'is introduced to give you time to cancel the runtime and '
          'reconfigure your preferred encoding, otherwise continue at own '
          'risk.')
      time.sleep(5)

    if self._process_archives:
      logging.warning(
          'Scanning archive files currently can cause deadlock. Continue at '
          'your own risk.')
      time.sleep(5)

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    self._command_line_arguments = self.GetCommandLineArguments()

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # The extraction options are dependent on the data location.
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['data_location'])

    # Check the list options first otherwise required options will raise.
    argument_helper_names = ['hashers', 'parsers']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseProfilingOptions(options)
    self._ParseTimezoneOption(options)

    self.list_hashers = self._hasher_names_string == 'list'
    self.list_parsers_and_plugins = self._parser_filter_expression == 'list'

    self.show_info = getattr(options, 'show_info', False)

    if getattr(options, 'use_markdown', False):
      self._views_format_type = views.ViewsFactory.FORMAT_TYPE_MARKDOWN

    self.dependencies_check = getattr(options, 'dependencies_check', True)

    if (self.list_hashers or self.list_parsers_and_plugins or
        self.list_profilers or self.list_timezones or self.show_info):
      return

    self._ParseInformationalOptions(options)

    argument_helper_names = [
        'artifact_definitions', 'extraction', 'filter_file', 'status_view',
        'storage_file', 'storage_format', 'text_prepend']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseLogFileOptions(options)

    self._ParseStorageMediaOptions(options)

    self._ParsePerformanceOptions(options)
    self._ParseProcessingOptions(options)

    format_string = (
        '%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
        '<%(module)s> %(message)s')

    if self._debug_mode:
      logging_level = logging.DEBUG
    elif self._quiet_mode:
      logging_level = logging.WARNING
    else:
      logging_level = logging.INFO

    self._ConfigureLogging(
        filename=self._log_file, format_string=format_string,
        log_level=logging_level)

    if self._debug_mode:
      log_filter = logging_filter.LoggingFilter()
      root_logger = logging.getLogger()
      root_logger.addFilter(log_filter)

    if not self._storage_file_path:
      raise errors.BadConfigOption('Missing storage file option.')

    serializer_format = getattr(
        options, 'serializer_format', definitions.SERIALIZER_FORMAT_JSON)
    if serializer_format not in definitions.SERIALIZER_FORMATS:
      raise errors.BadConfigOption(
          'Unsupported storage serializer format: {0:s}.'.format(
              serializer_format))
    self._storage_serializer_format = serializer_format

    # TODO: where is this defined?
    self._operating_system = getattr(options, 'os', None)

    if self._operating_system:
      self._mount_path = getattr(options, 'filename', None)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['status_view'])

    self._enable_sigsegv_handler = getattr(options, 'sigsegv_handler', False)

  def _PreprocessSources(self, extraction_engine):
    """Preprocesses the sources.

    Args:
      extraction_engine (BaseEngine): extraction engine to preprocess
          the sources.
    """
    logging.debug('Starting preprocessing.')

    try:
      extraction_engine.PreprocessSources(
          self._artifacts_registry, self._source_path_specs,
          resolver_context=self._resolver_context)

    except IOError as exception:
      logging.error('Unable to preprocess with error: {0:s}'.format(exception))

    logging.debug('Preprocessing done.')

  def ExtractEventsFromSources(self):
    """Processes the sources and extracts events.

    Raises:
      BadConfigOption: if the storage file path is invalid.
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    self._CheckStorageFile(self._storage_file_path)

    scan_context = self.ScanSource()
    self._source_type = scan_context.source_type

    self._status_view.SetMode(self._status_view_mode)
    self._status_view.SetSourceInformation(
        self._source_path, self._source_type, filter_file=self._filter_file)

    status_update_callback = (
        self._status_view.GetExtractionStatusUpdateCallback())

    self._output_writer.Write('\n')
    self._status_view.PrintExtractionStatusHeader(None)
    self._output_writer.Write('Processing started.\n')

    session = engine.BaseEngine.CreateSession(
        command_line_arguments=self._command_line_arguments,
        debug_mode=self._debug_mode,
        filter_file=self._filter_file,
        preferred_encoding=self.preferred_encoding,
        preferred_time_zone=self._preferred_time_zone,
        preferred_year=self._preferred_year)

    if self._storage_format == definitions.STORAGE_FORMAT_SQLITE:
      storage_writer = storage_sqlite_file.SQLiteStorageFileWriter(
          session, self._storage_file_path)

    else:
      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, self._storage_file_path)

    single_process_mode = self._single_process_mode
    if self._source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      # No need to multi process a single file source.
      single_process_mode = True

    if single_process_mode:
      extraction_engine = single_process_engine.SingleProcessEngine()
    else:
      extraction_engine = multi_process_engine.TaskMultiProcessEngine(
          use_zeromq=self._use_zeromq)

    # If the source is a directory or a storage media image
    # run pre-processing.
    if (self._force_preprocessing or
        self._source_type in self._SOURCE_TYPES_TO_PREPROCESS):
      self._PreprocessSources(extraction_engine)

    configuration = self._CreateProcessingConfiguration()

    if not configuration.parser_filter_expression:
      operating_system = extraction_engine.knowledge_base.GetValue(
          'operating_system')
      operating_system_product = extraction_engine.knowledge_base.GetValue(
          'operating_system_product')
      operating_system_version = extraction_engine.knowledge_base.GetValue(
          'operating_system_version')
      parser_filter_expression = (
          parsers_manager.ParsersManager.GetPresetForOperatingSystem(
              operating_system, operating_system_product,
              operating_system_version))

      if parser_filter_expression:
        logging.info('Parser filter expression changed to: {0:s}'.format(
            parser_filter_expression))

      configuration.parser_filter_expression = parser_filter_expression

      names_generator = parsers_manager.ParsersManager.GetParserAndPluginNames(
          parser_filter_expression=parser_filter_expression)

      session.enabled_parser_names = list(names_generator)
      session.parser_filter_expression = parser_filter_expression

    # Note session.preferred_time_zone will default to UTC but
    # self._preferred_time_zone is None when not set.
    if self._preferred_time_zone:
      try:
        extraction_engine.knowledge_base.SetTimeZone(self._preferred_time_zone)
      except ValueError:
        # pylint: disable=protected-access
        logging.warning(
            'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
                self._preferred_time_zone,
                extraction_engine.knowledge_base._time_zone.zone))

    filter_find_specs = None
    if configuration.filter_file:
      environment_variables = (
          extraction_engine.knowledge_base.GetEnvironmentVariables())
      filter_find_specs = frontend_utils.BuildFindSpecsFromFile(
          configuration.filter_file,
          environment_variables=environment_variables)

    processing_status = None
    if single_process_mode:
      logging.debug('Starting extraction in single process mode.')

      processing_status = extraction_engine.ProcessSources(
          self._source_path_specs, storage_writer, self._resolver_context,
          configuration, filter_find_specs=filter_find_specs,
          status_update_callback=status_update_callback)

    else:
      logging.debug('Starting extraction in multi process mode.')

      processing_status = extraction_engine.ProcessSources(
          session.identifier, self._source_path_specs, storage_writer,
          configuration, enable_sigsegv_handler=self._enable_sigsegv_handler,
          filter_find_specs=filter_find_specs,
          number_of_worker_processes=self._number_of_extraction_workers,
          status_update_callback=status_update_callback,
          worker_memory_limit=self._worker_memory_limit)

    self._status_view.PrintExtractionSummary(processing_status)

  def ShowInfo(self):
    """Shows information about available hashers, parsers, plugins, etc."""
    self._output_writer.Write(
        '{0:=^80s}\n'.format(' log2timeline/plaso information '))

    plugin_list = self._GetPluginData()
    for header, data in plugin_list.items():
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, column_names=['Name', 'Description'],
          title=header)
      for entry_header, entry_data in sorted(data):
        table_view.AddRow([entry_header, entry_data])
      table_view.Write(self._output_writer)
