# -*- coding: utf-8 -*-
"""The psort CLI tool."""

from __future__ import unicode_literals

import argparse
import collections
import os
import time

# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import

# The following import makes sure the formatters are registered.
from plaso import formatters  # pylint: disable=unused-import

# The following import makes sure the output modules are registered.
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import manager as analysis_manager
from plaso.cli import logger
from plaso.cli import status_view
from plaso.cli import time_slices
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import configurations
from plaso.engine import engine
from plaso.engine import knowledge_base
from plaso.filters import event_filter
from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import loggers
from plaso.lib import timelib
from plaso.multi_processing import psort
from plaso.storage import factory as storage_factory

import pytz  # pylint: disable=wrong-import-order


class PsortTool(
    tools.CLITool,
    tool_options.AnalysisPluginOptions,
    tool_options.OutputModuleOptions,
    tool_options.ProfilingOptions,
    tool_options.StorageFileOptions):
  """Psort CLI tool.

  Attributes:
    list_analysis_plugins (bool): True if information about the analysis
        plugins should be shown.
    list_language_identifiers (bool): True if information about the language
        identifiers should be shown.
    list_output_modules (bool): True if information about the output modules
        should be shown.
    list_profilers (bool): True if the profilers should be listed.
  """

  NAME = 'psort'
  DESCRIPTION = (
      'Application to read, filter and process output from a plaso storage '
      'file.')

  _FORMATTERS_FILE_NAME = 'formatters.yaml'

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
    self._analysis_manager = analysis_manager.AnalysisPluginManager
    self._analysis_plugins = None
    self._analysis_plugins_output_format = None
    self._command_line_arguments = None
    self._deduplicate_events = True
    self._event_filter_expression = None
    self._event_filter = None
    self._formatters_file = None
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._number_of_analysis_reports = 0
    self._preferred_language = 'en-US'
    self._process_memory_limit = None
    self._status_view_mode = status_view.StatusView.MODE_WINDOW
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._stdout_output_writer = isinstance(
        self._output_writer, tools.StdoutOutputWriter)
    self._storage_file_path = None
    self._temporary_directory = None
    self._time_slice = None
    self._use_time_slicer = False
    self._worker_memory_limit = None

    self.list_analysis_plugins = False
    self.list_language_identifiers = False
    self.list_output_modules = False
    self.list_profilers = False

  def _CheckStorageFile(self, storage_file_path):  # pylint: disable=arguments-differ
    """Checks if the storage file path is valid.

    Args:
      storage_file_path (str): path of the storage file.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))
      logger.warning('Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          'Unable to write to storage file: {0:s}'.format(storage_file_path))

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

  def _ParseFilterOptions(self, options):
    """Parses the filter options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._event_filter_expression = self.ParseStringOption(options, 'filter')
    if self._event_filter_expression:
      self._event_filter = event_filter.EventObjectFilter()

      try:
        self._event_filter.CompileFilter(self._event_filter_expression)
      except errors.ParseError as exception:
        raise errors.BadConfigOption((
            'Unable to compile filter expression with error: '
            '{0!s}').format(exception))

    time_slice_event_time_string = getattr(options, 'slice', None)
    time_slice_duration = getattr(options, 'slice_size', 5)
    self._use_time_slicer = getattr(options, 'slicer', False)

    # The slice and slicer cannot be set at the same time.
    if time_slice_event_time_string and self._use_time_slicer:
      raise errors.BadConfigOption(
          'Time slice and slicer cannot be used at the same time.')

    time_slice_event_timestamp = None
    if time_slice_event_time_string:
      # Note self._preferred_time_zone is None when not set but represents UTC.
      preferred_time_zone = self._preferred_time_zone or 'UTC'
      timezone = pytz.timezone(preferred_time_zone)
      time_slice_event_timestamp = timelib.Timestamp.FromTimeString(
          time_slice_event_time_string, timezone=timezone)
      if time_slice_event_timestamp is None:
        raise errors.BadConfigOption(
            'Unsupported time slice event date and time: {0:s}'.format(
                time_slice_event_time_string))

    if time_slice_event_timestamp is not None or self._use_time_slicer:
      # Note that time slicer uses the time slice to determine the duration.
      self._time_slice = time_slices.TimeSlice(
          time_slice_event_timestamp, duration=time_slice_duration)

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
      raise errors.BadConfigOption(
          'Invalid worker memory limit value cannot be negative.')

    self._worker_memory_limit = worker_memory_limit

  def _PrintAnalysisReportsDetails(self, storage_reader):
    """Prints the details of the analysis reports.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    for index, analysis_report in enumerate(
        storage_reader.GetAnalysisReports()):
      if index + 1 <= self._number_of_analysis_reports:
        continue

      title = 'Analysis report: {0:d}'.format(index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

  def _ReadEventFormattersFromFile(self):
    """Reads the event formatters the formatters.yaml file.

    Raises:
      BadConfigOption: if the event formatters file cannot be read.
    """
    self._formatters_file = os.path.join(
        self._data_location, self._FORMATTERS_FILE_NAME)
    if not os.path.isfile(self._formatters_file):
      raise errors.BadConfigOption(
          'No such event formatters file: {0:s}.'.format(self._formatters_file))

    try:
      formatters_manager.FormattersManager.ReadFormattersFromFile(
          self._formatters_file)
    except KeyError as exception:
      raise errors.BadConfigOption(
          'Unable to read event formatters from file with error: {0!s}'.format(
              exception))

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
        '--worker-memory-limit', '--worker_memory_limit',
        dest='worker_memory_limit', action='store', type=int,
        metavar='SIZE', help=(
            'Maximum amount of memory (data segment and shared memory) '
            'a worker process is allowed to consume in bytes, where 0 '
            'represents no limit. The default limit is 2147483648 (2 GiB). '
            'If a worker process exceeds this limit is is killed by the main '
            '(foreman) process.'))

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

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_parser, names=['storage_file'])

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

    self.AddTimeZoneOption(output_group)

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
      logger.warning(
          'The preferred encoding of your system is ASCII, which is not '
          'optimal for the typically non-ASCII characters that need to be '
          'parsed and processed. The tool will most likely crash and die, '
          'perhaps in a way that may not be recoverable. A five second delay '
          'is introduced to give you time to cancel the runtime and '
          'reconfigure your preferred encoding, otherwise continue at own '
          'risk.')
      time.sleep(5)

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_usage())

      return False

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
    # The output modules options are dependent on the preferred language
    # and preferred time zone options.
    self._ParseTimezoneOption(options)

    names = ['analysis_plugins', 'language', 'profiling']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=names)

    self.list_analysis_plugins = self._analysis_plugins == 'list'
    self.list_language_identifiers = self._preferred_language == 'list'
    self.list_profilers = self._profilers == 'list'

    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)

    if (self.list_analysis_plugins or self.list_language_identifiers or
        self.list_profilers or self.list_timezones or
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

    self._ReadEventFormattersFromFile()

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

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['storage_file'])

    # TODO: move check into _CheckStorageFile.
    if not self._storage_file_path:
      raise errors.BadConfigOption('Missing storage file option.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          'No such storage file: {0:s}.'.format(self._storage_file_path))

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

    self._analysis_plugins = self._CreateAnalysisPlugins(options)
    self._output_module = self._CreateOutputModule(options)

  def ProcessStorage(self):
    """Processes a plaso storage file.

    Raises:
      BadConfigOption: when a configuration parameter fails validation or the
          storage file cannot be opened with read access.
      RuntimeError: if a non-recoverable situation is encountered.
    """
    self._CheckStorageFile(self._storage_file_path)

    self._status_view.SetMode(self._status_view_mode)
    self._status_view.SetStorageFileInformation(self._storage_file_path)

    status_update_callback = (
        self._status_view.GetAnalysisStatusUpdateCallback())

    session = engine.BaseEngine.CreateSession(
        command_line_arguments=self._command_line_arguments,
        preferred_encoding=self.preferred_encoding)

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    if not storage_reader:
      raise errors.BadConfigOption(
          'Format of storage file: {0:s} not supported'.format(
              self._storage_file_path))

    self._number_of_analysis_reports = (
        storage_reader.GetNumberOfAnalysisReports())
    storage_reader.Close()

    configuration = configurations.ProcessingConfiguration()
    configuration.data_location = self._data_location
    configuration.profiling.directory = self._profiling_directory
    configuration.profiling.sample_rate = self._profiling_sample_rate
    configuration.profiling.profilers = self._profilers

    analysis_counter = None
    if self._analysis_plugins:
      storage_writer = (
          storage_factory.StorageFactory.CreateStorageWriterForFile(
              session, self._storage_file_path))
      if not storage_writer:
        raise errors.BadConfigOption(
            'Format of storage file: {0:s} not supported for writing'.format(
                self._storage_file_path))

      # TODO: add single processing support.
      analysis_engine = psort.PsortMultiProcessEngine()

      analysis_engine.AnalyzeEvents(
          self._knowledge_base, storage_writer, self._data_location,
          self._analysis_plugins, configuration,
          event_filter=self._event_filter,
          event_filter_expression=self._event_filter_expression,
          status_update_callback=status_update_callback,
          worker_memory_limit=self._worker_memory_limit)

      analysis_counter = collections.Counter()
      for item, value in iter(session.analysis_reports_counter.items()):
        analysis_counter[item] = value

    if self._output_format != 'null':
      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(
              self._storage_file_path))

      # TODO: add single processing support.
      analysis_engine = psort.PsortMultiProcessEngine()

      analysis_engine.ExportEvents(
          self._knowledge_base, storage_reader, self._output_module,
          configuration, deduplicate_events=self._deduplicate_events,
          event_filter=self._event_filter,
          status_update_callback=status_update_callback,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

    if self._quiet_mode:
      return

    self._output_writer.Write('Processing completed.\n')

    if analysis_counter:
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title='Analysis reports generated')
      for element, count in analysis_counter.most_common():
        if element != 'total':
          table_view.AddRow([element, count])

      table_view.AddRow(['Total', analysis_counter['total']])
      table_view.Write(self._output_writer)

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(storage_reader)
