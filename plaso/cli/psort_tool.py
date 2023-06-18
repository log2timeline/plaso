# -*- coding: utf-8 -*-
"""The psort CLI tool."""

import argparse
import os

# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import

# The following import makes sure the output modules are registered.
from plaso import output   # pylint: disable=unused-import

from plaso.cli import analysis_tool
from plaso.cli import logger
from plaso.cli import status_view
from plaso.cli import tool_options
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.containers import reports
from plaso.engine import configurations
from plaso.engine import engine
from plaso.helpers import language_tags
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import loggers
from plaso.multi_process import output_engine as multi_output_engine
from plaso.storage import factory as storage_factory


class PsortTool(
    analysis_tool.AnalysisTool,
    tool_options.OutputModuleOptions):
  """Psort CLI tool.

  Attributes:
    list_analysis_plugins (bool): True if information about the analysis
        plugins should be shown.
    list_language_tags (bool): True if the language tags should be listed.
    list_output_modules (bool): True if information about the output modules
        should be shown.
    list_profilers (bool): True if the profilers should be listed.
  """

  NAME = 'psort'
  DESCRIPTION = (
      'Application to read, filter and process output from a Plaso storage '
      'file.')

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(PsortTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._deduplicate_events = True
    self._preferred_language = None
    self._process_memory_limit = None
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._status_view_file = 'status.info'
    self._status_view_mode = status_view.StatusView.MODE_WINDOW
    self._time_slice = None
    self._use_time_slicer = False

    self.list_language_tags = False
    self.list_output_modules = False
    self.list_profilers = False

  def _CheckStorageFile(
      self, storage_file_path, check_readable_only=False):
    """Checks if the storage file is valid.

    Args:
      storage_file_path (str): path of the storage file.
      check_readable_only (Optional[bool]): whether the storage file should
          only be checked to see if it can be read. If False, the store will
          be checked to see if it can be read and written to.

    Raises:
      BadConfigOption: if the storage file is invalid.
    """
    if not storage_file_path:
      raise errors.BadConfigOption('Missing storage file option.')

    if not os.path.exists(storage_file_path):
      raise errors.BadConfigOption(
          'No such storage file: {0:s}.'.format(storage_file_path))

    if not os.path.isfile(storage_file_path):
      raise errors.BadConfigOption(
          'Storage file: {0:s} already exists and is not a file.'.format(
              storage_file_path))

    if not check_readable_only:
      storage_file_directory = os.path.dirname(storage_file_path) or '.'
      if not os.access(storage_file_directory, os.W_OK):
        raise errors.BadConfigOption(
            'Unable to write to storage file: {0:s}'.format(storage_file_path))

    storage_file = storage_factory.StorageFactory.CreateStorageFile(
        definitions.STORAGE_FORMAT_SQLITE)
    if not storage_file:
      raise errors.BadConfigOption(
          'Unable to open storage file: {0:s}'.format(storage_file_path))

    try:
      storage_file.Open(
          path=storage_file_path, read_only=check_readable_only)
    except IOError as exception:
      raise errors.BadConfigOption(
          'Unable to open storage file: {0:s} with error: {1!s}'.format(
              storage_file_path, exception))

    storage_file.Close()

  def _CreateOutputAndFormattingProcessingConfiguration(self):
    """Creates an output and formatting processing configuration.

    Returns:
      ProcessingConfiguration: output and formatting processing configuration.
    """
    configuration = configurations.ProcessingConfiguration()
    configuration.custom_formatters_path = self._output_custom_formatters_path
    configuration.data_location = self._data_location
    configuration.debug_output = self._debug_mode
    configuration.dynamic_time = self._output_dynamic_time
    configuration.log_filename = self._log_file
    configuration.preferred_language = self._preferred_language
    configuration.preferred_time_zone = self._output_time_zone
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.profilers = self._profilers
    configuration.profiling.sample_rate = self._profiling_sample_rate

    return configuration

  def _GetAnalysisPlugins(self, analysis_plugins_string):
    """Retrieves analysis plugins.

    Args:
      analysis_plugins_string (str): comma separated names of analysis plugins
          to enable.

    Returns:
      list[AnalysisPlugin]: analysis plugins.
    """
    if not analysis_plugins_string:
      return []

    analysis_plugins_list = [
        name.strip() for name in analysis_plugins_string.split(',')]

    analysis_plugins = self._analysis_manager.GetPluginObjects(
        analysis_plugins_list)
    return analysis_plugins.values()

  def _ParseAnalysisPluginOptions(self, options):
    """Parses the analysis plugin options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # Get a list of all available plugins.
    analysis_plugin_info = self._analysis_manager.GetAllPluginInformation()
    # Use set-comprehension to create a set of the analysis plugin names.
    analysis_plugin_names = {
        name.lower() for name, _, _ in analysis_plugin_info}

    analysis_plugins = self.ParseStringOption(options, 'analysis_plugins')
    if not analysis_plugins:
      return

    # Use set-comprehension to create a set of the requested plugin names.
    requested_plugin_names = {
        name.strip().lower() for name in analysis_plugins.split(',')}

    # Check to see if we are trying to load plugins that do not exist.
    difference = requested_plugin_names.difference(analysis_plugin_names)
    if difference:
      raise errors.BadConfigOption(
          'Non-existent analysis plugins specified: {0:s}'.format(
              ' '.join(difference)))

    self._analysis_plugins = self._GetAnalysisPlugins(analysis_plugins)

    for analysis_plugin in self._analysis_plugins:
      helpers_manager.ArgumentHelperManager.ParseOptions(
          options, analysis_plugin)

  def _ParseInformationalOptions(self, options):
    """Parses the informational options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PsortTool, self)._ParseInformationalOptions(options)

    self._quiet_mode = getattr(options, 'quiet', False)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['status_view'])

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    argument_helper_names = [
        'process_resources', 'temporary_directory', 'zeromq']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    worker_memory_limit = getattr(options, 'worker_memory_limit', None)

    if worker_memory_limit and worker_memory_limit < 0:
      raise errors.BadConfigOption((
          'Invalid worker memory limit: {0:d}, value must be 0 or '
          'greater.').format(worker_memory_limit))

    worker_timeout = getattr(options, 'worker_timeout', None)

    if worker_timeout is not None and worker_timeout <= 0.0:
      raise errors.BadConfigOption((
          'Invalid worker timeout: {0:f}, value must be greater than '
          '0.0 minutes.').format(worker_timeout))

    self._worker_memory_limit = worker_memory_limit
    self._worker_timeout = worker_timeout

  def AddProcessingOptions(self, argument_group):
    """Adds processing options to the argument group

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_helper_names = ['temporary_directory', 'zeromq']
    if self._CanEnforceProcessMemoryLimit():
      argument_helper_names.append('process_resources')
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=argument_helper_names)

    argument_group.add_argument(
        '--worker_memory_limit', '--worker-memory-limit',
        dest='worker_memory_limit', action='store', type=int,
        metavar='SIZE', help=(
            'Maximum amount of memory (data segment and shared memory) '
            'a worker process is allowed to consume in bytes, where 0 '
            'represents no limit. The default limit is 2147483648 (2 GiB). '
            'If a worker process exceeds this limit it is killed by the main '
            '(foreman) process.'))

    argument_group.add_argument(
        '--worker_timeout', '--worker-timeout', dest='worker_timeout',
        action='store', type=float, metavar='MINUTES', help=(
            'Number of minutes before a worker process that is not providing '
            'status updates is considered inactive. The default timeout is '
            '15.0 minutes. If a worker process exceeds this timeout it is '
            'killed by the main (foreman) process.'))

  def ListLanguageTags(self):
    """Lists the language tags."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Language tag', 'Description'],
        title='Language tags')
    for language_tag, description in (
        language_tags.LanguageTagHelper.GetLanguages()):
      table_view.AddRow([language_tag, description])
    table_view.Write(self._output_writer)

  def ParseArguments(self, arguments):
    """Parses the command line arguments.

    Args:
      arguments (list[str]): command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    loggers.ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False,
        conflict_handler='resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddStorageOptions(argument_parser)

    analysis_group = argument_parser.add_argument_group('Analysis Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        analysis_group, names=['analysis_plugins'])

    processing_group = argument_parser.add_argument_group('Processing')
    self.AddProcessingOptions(processing_group)

    info_group = argument_parser.add_argument_group('Informational Arguments')

    self.AddLogFileOptions(info_group)
    self.AddInformationalOptions(info_group)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        info_group, names=['status_view'])

    filter_group = argument_parser.add_argument_group('Filter Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        filter_group, names=['event_filters'])

    input_group = argument_parser.add_argument_group('Input Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        input_group, names=['data_location'])

    output_group = argument_parser.add_argument_group('Output Arguments')

    output_group.add_argument(
        '-a', '--include_all', '--include-all', action='store_false',
        dest='dedup', default=True, help=(
            'By default the psort removes duplicate entries from the '
            'output. This parameter changes that behavior so all events '
            'are included.'))

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_group, names=['language'])

    self.AddOutputOptions(output_group)

    output_format_group = argument_parser.add_argument_group(
        'Output Format Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_format_group, names=['output_modules'])

    profiling_group = argument_parser.add_argument_group('profiling arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        profiling_group, names=['profiling'])

    try:
      # TODO: refactor how arguments is used in a more argparse way.
      options = argument_parser.parse_args(arguments)
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    # Properly prepare the attributes according to local encoding.
    if self.preferred_encoding == 'ascii':
      self._PrintUserWarning((
          'the preferred encoding of your system is ASCII, which is not '
          'optimal for the typically non-ASCII characters that need to be '
          'parsed and processed. This will most likely result in an error.'))

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_usage())

      return False

    self._WaitUserWarning()

    loggers.ConfigureLogging(
        debug_output=self._debug_mode, filename=self._log_file,
        quiet_mode=self._quiet_mode)

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # The output modules options are dependent on the preferred_language
    # and output_time_zone options.
    self._ParseOutputOptions(options)

    names = ['analysis_plugins', 'language', 'profiling']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=names)

    self.list_analysis_plugins = self._analysis_plugins == 'list'
    self.list_language_tags = self._preferred_language == 'list'
    self.list_profilers = self._profilers == 'list'

    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)

    if (self.list_analysis_plugins or self.list_language_tags or
        self.list_profilers or self.list_time_zones or
        self.show_troubleshooting):
      return

    # Check output modules after the other listable options, otherwise
    # it could raise with "requires an output file".
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['output_modules'])

    self.list_output_modules = self._output_format == 'list'
    if self.list_output_modules:
      return

    self._ParseInformationalOptions(options)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['data_location'])

    self._ParseLogFileOptions(options)

    self._ParseProcessingOptions(options)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['event_filters'])

    self._deduplicate_events = getattr(options, 'dedup', True)

    if self._data_location:
      # Update the data location with the calculated value.
      options.data_location = self._data_location
    else:
      logger.warning('Unable to automatically determine data location.')

    self._command_line_arguments = self.GetCommandLineArguments()

    self._storage_file_path = self.ParseStringOption(options, 'storage_file')

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

    self._analysis_plugins = self._CreateAnalysisPlugins(options)
    self._output_module = self._CreateOutputModule(options)

    check_readable_only = not self._analysis_plugins
    self._CheckStorageFile(
        self._storage_file_path, check_readable_only=check_readable_only)

  def ProcessStorage(self):
    """Processes a Plaso storage file.

    Raises:
      BadConfigOption: when a configuration parameter fails validation or the
          storage file cannot be opened with read access.
      RuntimeError: if a non-recoverable situation is encountered.
    """
    self._status_view.SetMode(self._status_view_mode)
    self._status_view.SetStatusFile(self._status_view_file)
    self._status_view.SetStorageFileInformation(self._storage_file_path)

    status_update_callback = (
        self._status_view.GetAnalysisStatusUpdateCallback())

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    if not storage_reader:
      raise RuntimeError('Unable to create storage reader.')

    try:
      self._number_of_stored_analysis_reports = (
          storage_reader.GetNumberOfAttributeContainers(
              self._CONTAINER_TYPE_ANALYSIS_REPORT))
    finally:
      storage_reader.Close()

    session = engine.BaseEngine.CreateSession()

    configuration = self._CreateOutputAndFormattingProcessingConfiguration()

    # TODO: implement _CreateAnalysisProcessingConfiguration

    if self._analysis_plugins:
      self._AnalyzeEvents(
          session, configuration, status_update_callback=status_update_callback)

    # TODO: abort if session.aborted is True

    if self._output_format != 'null':
      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(
              self._storage_file_path))

      # TODO: add single process output and formatting engine support.
      output_engine = (
          multi_output_engine.OutputAndFormattingMultiProcessEngine())

      output_engine.SetStatusUpdateInterval(self._status_view_interval)

      output_engine.ExportEvents(
          storage_reader, self._output_module, configuration,
          deduplicate_events=self._deduplicate_events,
          event_filter=self._event_filter,
          status_update_callback=status_update_callback,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

      self._output_module.Close()
      self._output_module = None

    if self._quiet_mode:
      return

    self._output_writer.Write('Processing completed.\n')

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(storage_reader)
