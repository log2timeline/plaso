# -*- coding: utf-8 -*-
"""The psort CLI tool."""

import argparse
import collections
import logging
import os
import sys
import time

# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import

# The following import makes sure the formatters are registered.
from plaso import formatters  # pylint: disable=unused-import

# The following import makes sure the output modules are registered.
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import manager as analysis_manager
from plaso.cli import status_view
from plaso.cli import time_slices
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import configurations
from plaso.engine import engine
from plaso.engine import knowledge_base
from plaso.filters import manager as filters_manager
from plaso.lib import errors
from plaso.lib import timelib
from plaso.multi_processing import psort
from plaso.storage import factory as storage_factory
from plaso.winnt import language_ids

import pytz


class PsortTool(
    tools.CLITool,
    tool_options.AnalysisPluginOptions,
    tool_options.OutputModuleOptions,
    tool_options.StorageFileOptions):
  """Psort CLI tool.

  Attributes:
    list_analysis_plugins (bool): True if information about the analysis
        plugins should be shown.
    list_language_identifiers (bool): True if information about the language
        identifiers should be shown.
    list_output_modules (bool): True if information about the output modules
        should be shown.
  """

  NAME = u'psort'
  DESCRIPTION = (
      u'Application to read, filter and process output from a plaso storage '
      u'file.')

  # The window status-view mode has an annoying flicker on Windows,
  # hence we default to linear status-view mode instead.
  if sys.platform.startswith(u'win'):
    _DEFAULT_STATUS_VIEW_MODE = status_view.StatusView.MODE_LINEAR
  else:
    _DEFAULT_STATUS_VIEW_MODE = status_view.StatusView.MODE_WINDOW

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
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._number_of_analysis_reports = 0
    self._preferred_language = u'en-US'
    self._status_view_mode = self._DEFAULT_STATUS_VIEW_MODE
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._stdout_output_writer = isinstance(
        self._output_writer, tools.StdoutOutputWriter)
    self._storage_file_path = None
    self._temporary_directory = None
    self._time_slice = None
    self._use_time_slicer = False
    self._use_zeromq = True
    self._worker_memory_limit = None

    self.list_analysis_plugins = False
    self.list_language_identifiers = False
    self.list_output_modules = False

  def _CheckStorageFile(self, storage_file_path):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path (str): path of the storage file.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            u'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))
      logging.warning(u'Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = u'.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          u'Unable to write to storage file: {0:s}'.format(storage_file_path))

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
        name.strip() for name in analysis_plugins_string.split(u',')]

    analysis_plugins = self._analysis_manager.GetPluginObjects(
        analysis_plugins_list)
    return analysis_plugins.values()

  def _ParseAnalysisPluginOptions(self, options):
    """Parses the analysis plugin options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    # Get a list of all available plugins.
    analysis_plugin_info = self._analysis_manager.GetAllPluginInformation()
    analysis_plugin_names = set([
        name.lower() for name, _, _ in analysis_plugin_info])

    analysis_plugins = self.ParseStringOption(options, u'analysis_plugins')
    if not analysis_plugins:
      return

    requested_plugin_names = set([
        name.strip().lower() for name in analysis_plugins.split(u',')])

    # Check to see if we are trying to load plugins that do not exist.
    difference = requested_plugin_names.difference(analysis_plugin_names)
    if difference:
      raise errors.BadConfigOption(
          u'Non-existent analysis plugins specified: {0:s}'.format(
              u' '.join(difference)))

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
    self._event_filter_expression = self.ParseStringOption(options, u'filter')
    if self._event_filter_expression:
      self._event_filter = filters_manager.FiltersManager.GetFilterObject(
          self._event_filter_expression)
      if not self._event_filter:
        raise errors.BadConfigOption(u'Invalid filter expression: {0:s}'.format(
            self._event_filter_expression))

    time_slice_event_time_string = getattr(options, u'slice', None)
    time_slice_duration = getattr(options, u'slice_size', 5)
    self._use_time_slicer = getattr(options, u'slicer', False)

    # The slice and slicer cannot be set at the same time.
    if time_slice_event_time_string and self._use_time_slicer:
      raise errors.BadConfigOption(
          u'Time slice and slicer cannot be used at the same time.')

    time_slice_event_timestamp = None
    if time_slice_event_time_string:
      preferred_time_zone = self._preferred_time_zone or u'UTC'
      timezone = pytz.timezone(preferred_time_zone)
      time_slice_event_timestamp = timelib.Timestamp.FromTimeString(
          time_slice_event_time_string, timezone=timezone)
      if time_slice_event_timestamp is None:
        raise errors.BadConfigOption(
            u'Unsupported time slice event date and time: {0:s}'.format(
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

    self._quiet_mode = getattr(options, u'quiet', False)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'status_view'])

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    self._use_zeromq = getattr(options, u'use_zeromq', True)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'temporary_directory'])

    self._worker_memory_limit = getattr(options, u'worker_memory_limit', None)

  def _PrintAnalysisReportsDetails(self, storage):
    """Prints the details of the analysis reports.

    Args:
      storage (BaseStorage): storage writer.
    """
    for index, analysis_report in enumerate(storage.GetAnalysisReports()):
      if index + 1 <= self._number_of_analysis_reports:
        continue

      title = u'Analysis report: {0:d}'.format(index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

  def AddProcessingOptions(self, argument_group):
    """Adds processing options to the argument group

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--disable_zeromq', u'--disable-zeromq', action=u'store_false',
        dest=u'use_zeromq', default=True, help=(
            u'Disable queueing using ZeroMQ. A Multiprocessing queue will be '
            u'used instead.'))

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=[u'temporary_directory'])

    argument_group.add_argument(
        u'--worker-memory-limit', u'--worker_memory_limit',
        dest=u'worker_memory_limit', action=u'store', type=int,
        metavar=u'SIZE', help=(
            u'Maximum amount of memory a worker process is allowed to consume. '
            u'[defaults to 2 GiB]'))

  def ListLanguageIdentifiers(self):
    """Lists the language identifiers."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Identifier', u'Language'],
        title=u'Language identifiers')
    for language_id, value_list in sorted(
        language_ids.LANGUAGE_IDENTIFIERS.items()):
      table_view.AddRow([language_id, value_list[1]])
    table_view.Write(self._output_writer)

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False,
        conflict_handler=u'resolve',
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_parser, names=[u'storage_file'])

    analysis_group = argument_parser.add_argument_group(u'Analysis Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        analysis_group, names=[u'analysis_plugins'])

    processing_group = argument_parser.add_argument_group(u'Processing')
    self.AddProcessingOptions(processing_group)

    info_group = argument_parser.add_argument_group(u'Informational Arguments')

    self.AddLogFileOptions(info_group)
    self.AddInformationalOptions(info_group)

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        info_group, names=[u'status_view'])

    filter_group = argument_parser.add_argument_group(u'Filter Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        filter_group, names=[u'event_filters'])

    input_group = argument_parser.add_argument_group(u'Input Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        input_group, names=[u'data_location'])

    output_group = argument_parser.add_argument_group(u'Output Arguments')

    output_group.add_argument(
        u'-a', u'--include_all', u'--include-all', action=u'store_false',
        dest=u'dedup', default=True, help=(
            u'By default the psort removes duplicate entries from the '
            u'output. This parameter changes that behavior so all events '
            u'are included.'))

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_group, names=[u'language'])

    self.AddTimeZoneOption(output_group)

    output_format_group = argument_parser.add_argument_group(
        u'Output Format Arguments')

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        output_format_group, names=[u'output_modules'])

    try:
      # TODO: refactor how arguments is used in a more argparse way.
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

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write(u'ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_usage())

      return False

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # Check the list options first otherwise required options will raise.

    # The output modules options are dependent on the preferred language
    # and preferred time zone options.
    self._ParseTimezoneOption(options)

    names = [u'analysis_plugins', u'language', u'output_modules']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=names)

    if self._output_format == u'list':
      self.list_output_modules = True
    if self._preferred_language == u'list':
      self.list_language_identifiers = True

    if (self.list_analysis_plugins or self.list_language_identifiers or
        self.list_output_modules or self.list_timezones):
      return

    self._ParseInformationalOptions(options)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'data_location'])

    self._ParseLogFileOptions(options)

    self._ParseProcessingOptions(options)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'event_filters'])

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

    self._deduplicate_events = getattr(options, u'dedup', True)

    if self._data_location:
      # Update the data location with the calculated value.
      options.data_location = self._data_location
    else:
      logging.warning(u'Unable to automatically determine data location.')

    self._command_line_arguments = self.GetCommandLineArguments()

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'storage_file'])

    # TODO: move check into _CheckStorageFile.
    if not self._storage_file_path:
      raise errors.BadConfigOption(u'Missing storage file option.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          u'No such storage file: {0:s}.'.format(self._storage_file_path))

    self._analysis_plugins = self._CreateAnalysisPlugins(options)
    self._output_module = self._CreateOutputModule(options)

  def ProcessStorage(self):
    """Processes a plaso storage file.

    Raises:
      BadConfigOption: when a configuration parameter fails validation.
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
      logging.error(
          u'Format of storage file: {0:s} not supported'.format(
              self._storage_file_path))
      return

    self._number_of_analysis_reports = (
        storage_reader.GetNumberOfAnalysisReports())
    storage_reader.Close()

    configuration = configurations.ProcessingConfiguration()
    configuration.data_location = self._data_location

    analysis_counter = None
    if self._analysis_plugins:
      storage_writer = (
          storage_factory.StorageFactory.CreateStorageWriterForFile(
              session, self._storage_file_path))

      # TODO: add single processing support.
      analysis_engine = psort.PsortMultiProcessEngine(
          use_zeromq=self._use_zeromq)

      # TODO: pass configuration object.
      analysis_engine.AnalyzeEvents(
          self._knowledge_base, storage_writer, self._data_location,
          self._analysis_plugins, event_filter=self._event_filter,
          event_filter_expression=self._event_filter_expression,
          status_update_callback=status_update_callback)

      analysis_counter = collections.Counter()
      for item, value in iter(session.analysis_reports_counter.items()):
        analysis_counter[item] = value

    events_counter = None
    if self._output_format != u'null':
      storage_reader = (
          storage_factory.StorageFactory.CreateStorageReaderForFile(
              self._storage_file_path))

      # TODO: add single processing support.
      analysis_engine = psort.PsortMultiProcessEngine(
          use_zeromq=self._use_zeromq)

      # TODO: pass configuration object.
      events_counter = analysis_engine.ExportEvents(
          self._knowledge_base, storage_reader, self._output_module,
          deduplicate_events=self._deduplicate_events,
          event_filter=self._event_filter,
          status_update_callback=status_update_callback,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

    if self._quiet_mode:
      return

    self._output_writer.Write(u'Processing completed.\n')

    if analysis_counter:
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=u'Analysis reports generated')
      for element, count in analysis_counter.most_common():
        if element != u'total':
          table_view.AddRow([element, count])

      table_view.AddRow([u'Total', analysis_counter[u'total']])
      table_view.Write(self._output_writer)

    if events_counter:
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=u'Export results')
      for element, count in events_counter.most_common():
        table_view.AddRow([element, count])
      table_view.Write(self._output_writer)

    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(storage_reader)
