# -*- coding: utf-8 -*-
"""The log2timeline CLI tool."""

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

  NAME = u'log2timeline'
  DESCRIPTION = textwrap.dedent(u'\n'.join([
      u'',
      (u'log2timeline is a command line tool to extract events from '
       u'individual '),
      u'files, recursing a directory (e.g. mount point) or storage media ',
      u'image or device.',
      u'',
      u'More information can be gathered from here:',
      u'    https://github.com/log2timeline/plaso/wiki/Using-log2timeline',
      u'']))

  EPILOG = textwrap.dedent(u'\n'.join([
      u'',
      u'Example usage:',
      u'',
      u'Run the tool against a storage media image (full kitchen sink)',
      u'    log2timeline.py /cases/mycase/storage.plaso ímynd.dd',
      u'',
      u'Instead of answering questions, indicate some of the options on the',
      u'command line (including data from particular VSS stores).',
      (u'    log2timeline.py -o 63 --vss_stores 1,2 /cases/plaso_vss.plaso '
       u'image.E01'),
      u'',
      u'And that is how you build a timeline using log2timeline...',
      u'']))

  # The window status-view mode has an annoying flicker on Windows,
  # hence we default to linear status-view mode instead.
  if sys.platform.startswith(u'win'):
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

    return_dict[u'Versions'] = [
        (u'plaso engine', plaso.__version__),
        (u'python', sys.version)]

    hashers_information = hashers_manager.HashersManager.GetHashersInformation()
    parsers_information = parsers_manager.ParsersManager.GetParsersInformation()
    plugins_information = (
        parsers_manager.ParsersManager.GetParserPluginsInformation())
    presets_information = self._GetParserPresetsInformation()

    return_dict[u'Hashers'] = hashers_information
    return_dict[u'Parsers'] = parsers_information
    return_dict[u'Parser Plugins'] = plugins_information
    return_dict[u'Parser Presets'] = presets_information

    return return_dict

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._use_zeromq = getattr(options, u'use_zeromq', True)

    self._single_process_mode = getattr(options, u'single_process', False)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'temporary_directory'])

    self._worker_memory_limit = getattr(options, u'worker_memory_limit', None)
    self._number_of_extraction_workers = getattr(options, u'workers', 0)

    # TODO: add code to parse the worker options.

  def AddProcessingOptions(self, argument_group):
    """Adds the processing options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--disable_zeromq', u'--disable-zeromq', action=u'store_false',
        dest=u'use_zeromq', default=True, help=(
            u'Disable queueing using ZeroMQ. A Multiprocessing queue will be '
            u'used instead.'))

    argument_group.add_argument(
        u'--single_process', u'--single-process', dest=u'single_process',
        action=u'store_true', default=False, help=(
            u'Indicate that the tool should run in a single process.'))

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=[u'temporary_directory'])

    argument_group.add_argument(
        u'--worker-memory-limit', u'--worker_memory_limit',
        dest=u'worker_memory_limit', action=u'store', type=int,
        metavar=u'SIZE', help=(
            u'Maximum amount of memory a worker process is allowed to consume. '
            u'[defaults to 2 GiB]'))

    argument_group.add_argument(
        u'--workers', dest=u'workers', action=u'store', type=int, default=0,
        help=(u'The number of worker processes [defaults to available system '
              u'CPUs minus one].'))

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
        argument_parser, names=[u'storage_file', u'storage_format'])

    extraction_group = argument_parser.add_argument_group(
        u'Extraction Arguments')

    argument_helper_names = [
        u'artifact_definitions', u'extraction', u'filter_file', u'hashers',
        u'parsers', u'yara_rules']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        extraction_group, names=argument_helper_names)

    self.AddStorageMediaImageOptions(extraction_group)
    self.AddTimeZoneOption(extraction_group)
    self.AddVSSProcessingOptions(extraction_group)
    self.AddCredentialOptions(extraction_group)

    info_group = argument_parser.add_argument_group(u'Informational Arguments')

    self.AddInformationalOptions(info_group)

    info_group.add_argument(
        u'--info', dest=u'show_info', action=u'store_true', default=False,
        help=u'Print out information about supported plugins and parsers.')

    info_group.add_argument(
        u'--use_markdown', u'--use-markdown', dest=u'use_markdown',
        action=u'store_true', default=False, help=(
            u'Output lists in Markdown format use in combination with '
            u'"--hashers list", "--parsers list" or "--timezone list"'))

    info_group.add_argument(
        u'--no_dependencies_check', u'--no-dependencies-check',
        dest=u'dependencies_check', action=u'store_false', default=True,
        help=u'Disable the dependencies check.')

    self.AddLogFileOptions(info_group)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        info_group, names=[u'status_view'])

    output_group = argument_parser.add_argument_group(u'Output Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_group, names=[u'text_prepend'])

    processing_group = argument_parser.add_argument_group(
        u'Processing Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        processing_group, names=[u'data_location'])

    self.AddPerformanceOptions(processing_group)
    self.AddProfilingOptions(processing_group)
    self.AddProcessingOptions(processing_group)

    processing_group.add_argument(
        u'--sigsegv_handler', u'--sigsegv-handler', dest=u'sigsegv_handler',
        action=u'store_true', default=False, help=(
            u'Enables the SIGSEGV handler. WARNING this functionality is '
            u'experimental and will a deadlock worker process if a real '
            u'segfault is caught, but not signal SIGSEGV. This functionality '
            u'is therefore primarily intended for debugging purposes'))

    argument_parser.add_argument(
        self._SOURCE_OPTION, action=u'store', metavar=u'SOURCE', nargs=u'?',
        default=None, type=str, help=(
            u'The path to the source device, file or directory. If the source '
            u'is a supported storage media device or image file, archive file '
            u'or a directory, the files within are processed recursively.'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    # Properly prepare the attributes according to local encoding.
    if self.preferred_encoding == u'ascii':
      logging.warning(
          u'The preferred encoding of your system is ASCII, which is not '
          u'optimal for the typically non-ASCII characters that need to be '
          u'parsed and processed. The tool will most likely crash and die, '
          u'perhaps in a way that may not be recoverable. A five second delay '
          u'is introduced to give you time to cancel the runtime and '
          u'reconfigure your preferred encoding, otherwise continue at own '
          u'risk.')
      time.sleep(5)

    if self._process_archives:
      logging.warning(
          u'Scanning archive files currently can cause deadlock. Continue at '
          u'your own risk.')
      time.sleep(5)

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write(u'ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write(u'\n')
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
        options, self, names=[u'data_location'])

    # Check the list options first otherwise required options will raise.
    argument_helper_names = [u'hashers', u'parsers']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseProfilingOptions(options)
    self._ParseTimezoneOption(options)

    self.list_hashers = self._hasher_names_string == u'list'
    self.list_parsers_and_plugins = self._parser_filter_expression == u'list'

    self.show_info = getattr(options, u'show_info', False)

    if getattr(options, u'use_markdown', False):
      self._views_format_type = views.ViewsFactory.FORMAT_TYPE_MARKDOWN

    self.dependencies_check = getattr(options, u'dependencies_check', True)

    if (self.list_hashers or self.list_parsers_and_plugins or
        self.list_profilers or self.list_timezones or self.show_info):
      return

    self._ParseInformationalOptions(options)

    argument_helper_names = [
        u'artifact_definitions', u'extraction', u'filter_file', u'status_view',
        u'storage_file', u'storage_format', u'text_prepend']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    self._ParseLogFileOptions(options)

    self._ParseStorageMediaOptions(options)

    self._ParsePerformanceOptions(options)
    self._ParseProcessingOptions(options)

    format_string = (
        u'%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
        u'<%(module)s> %(message)s')

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
      raise errors.BadConfigOption(u'Missing storage file option.')

    serializer_format = getattr(
        options, u'serializer_format', definitions.SERIALIZER_FORMAT_JSON)
    if serializer_format not in definitions.SERIALIZER_FORMATS:
      raise errors.BadConfigOption(
          u'Unsupported storage serializer format: {0:s}.'.format(
              serializer_format))
    self._storage_serializer_format = serializer_format

    # TODO: where is this defined?
    self._operating_system = getattr(options, u'os', None)

    if self._operating_system:
      self._mount_path = getattr(options, u'filename', None)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'status_view'])

    self._enable_sigsegv_handler = getattr(options, u'sigsegv_handler', False)

  def _PreprocessSources(self, extraction_engine):
    """Preprocesses the sources.

    Args:
      extraction_engine (BaseEngine): extraction engine to preprocess
          the sources.
    """
    logging.debug(u'Starting preprocessing.')

    try:
      extraction_engine.PreprocessSources(
          self._artifacts_registry, self._source_path_specs,
          resolver_context=self._resolver_context)

    except IOError as exception:
      logging.error(u'Unable to preprocess with error: {0:s}'.format(exception))

    logging.debug(u'Preprocessing done.')

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

    self._output_writer.Write(u'\n')
    self._status_view.PrintExtractionStatusHeader(None)
    self._output_writer.Write(u'Processing started.\n')

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
          u'operating_system')
      operating_system_product = extraction_engine.knowledge_base.GetValue(
          u'operating_system_product')
      operating_system_version = extraction_engine.knowledge_base.GetValue(
          u'operating_system_version')
      parser_filter_expression = (
          parsers_manager.ParsersManager.GetPresetForOperatingSystem(
              operating_system, operating_system_product,
              operating_system_version))

      if parser_filter_expression:
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            parser_filter_expression))

      configuration.parser_filter_expression = parser_filter_expression

      names_generator = parsers_manager.ParsersManager.GetParserAndPluginNames(
          parser_filter_expression=parser_filter_expression)

      session.enabled_parser_names = list(names_generator)
      session.parser_filter_expression = parser_filter_expression

    if session.preferred_time_zone:
      try:
        extraction_engine.knowledge_base.SetTimeZone(
            session.preferred_time_zone)
      except ValueError:
        # pylint: disable=protected-access
        logging.warning(
            u'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
                session.preferred_time_zone,
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
      logging.debug(u'Starting extraction in single process mode.')

      processing_status = extraction_engine.ProcessSources(
          self._source_path_specs, storage_writer, self._resolver_context,
          configuration, filter_find_specs=filter_find_specs,
          status_update_callback=status_update_callback)

    else:
      logging.debug(u'Starting extraction in multi process mode.')

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
        u'{0:=^80s}\n'.format(u' log2timeline/plaso information '))

    plugin_list = self._GetPluginData()
    for header, data in plugin_list.items():
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, column_names=[u'Name', u'Description'],
          title=header)
      for entry_header, entry_data in sorted(data):
        table_view.AddRow([entry_header, entry_data])
      table_view.Write(self._output_writer)
