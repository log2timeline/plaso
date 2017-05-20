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

from plaso.cli import status_view
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.engine import configurations
from plaso.engine import engine
from plaso.engine import knowledge_base
from plaso.lib import errors
from plaso.multi_processing import psort
from plaso.storage import zip_file as storage_zip_file


class PsortTool(
    tools.CLITool,
    tool_options.AnalysisPluginOptions,
    tool_options.FilterOptions,
    tool_options.LanguageOptions,
    tool_options.OutputModuleOptions,
    tool_options.StorageFileOptions):
  """Psort CLI tool."""

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
    self._analysis_plugins_output_format = None
    self._command_line_arguments = None
    self._deduplicate_events = True
    self._number_of_analysis_reports = 0
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._status_view_mode = self._DEFAULT_STATUS_VIEW_MODE
    self._stdout_output_writer = isinstance(
        self._output_writer, tools.StdoutOutputWriter)
    self._temporary_directory = None
    self._use_zeromq = True
    self._worker_memory_limit = None

  def _ParseInformationalOptions(self, options):
    """Parses the informational options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PsortTool, self)._ParseInformationalOptions(options)

    self._quiet_mode = getattr(options, u'quiet', False)

    self._status_view_mode = getattr(
        options, u'status_view_mode', self._DEFAULT_STATUS_VIEW_MODE)

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    self._use_zeromq = getattr(options, u'use_zeromq', True)

    self._temporary_directory = getattr(options, u'temporary_directory', None)
    if (self._temporary_directory and
        not os.path.isdir(self._temporary_directory)):
      raise errors.BadConfigOption(
          u'No such temporary directory: {0:s}'.format(
              self._temporary_directory))

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

    argument_group.add_argument(
        u'--temporary_directory', u'--temporary-directory',
        dest=u'temporary_directory', type=str, action=u'store',
        metavar=u'DIRECTORY', help=(
            u'Path to the directory that should be used to store temporary '
            u'files created during analysis.'))

    argument_group.add_argument(
        u'--worker-memory-limit', u'--worker_memory_limit',
        dest=u'worker_memory_limit', action=u'store', type=int,
        metavar=u'SIZE', help=(
            u'Maximum amount of memory a worker process is allowed to consume. '
            u'[defaults to 2 GiB]'))

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
    self.AddStorageFileOptions(argument_parser)

    analysis_group = argument_parser.add_argument_group(u'Analysis Arguments')

    analysis_group.add_argument(
        u'--analysis', metavar=u'PLUGIN_LIST', dest=u'analysis_plugins',
        default=u'', action=u'store', type=str, help=(
            u'A comma separated list of analysis plugin names to be loaded '
            u'or "--analysis list" to see a list of available plugins.'))

    processing_group = argument_parser.add_argument_group(u'Processing')
    self.AddProcessingOptions(processing_group)

    info_group = argument_parser.add_argument_group(u'Informational Arguments')

    self.AddLogFileOptions(info_group)
    self.AddInformationalOptions(info_group)

    info_group.add_argument(
        u'--status_view', u'--status-view', dest=u'status_view_mode',
        choices=[u'linear', u'none', u'window'], action=u'store',
        metavar=u'TYPE', default=self._DEFAULT_STATUS_VIEW_MODE, help=(
            u'The processing status view mode: "linear", "none" or "window".'))

    filter_group = argument_parser.add_argument_group(u'Filter Arguments')

    self.AddFilterOptions(filter_group)

    input_group = argument_parser.add_argument_group(u'Input Arguments')

    self.AddDataLocationOption(input_group)

    output_group = argument_parser.add_argument_group(u'Output Arguments')

    output_group.add_argument(
        u'-a', u'--include_all', u'--include-all', action=u'store_false',
        dest=u'dedup', default=True, help=(
            u'By default the psort removes duplicate entries from the '
            u'output. This parameter changes that behavior so all events '
            u'are included.'))

    self.AddLanguageOptions(output_group)
    self.AddTimeZoneOption(output_group)

    output_format_group = argument_parser.add_argument_group(
        u'Output Format Arguments')

    self.AddOutputModuleOptions(output_format_group)

    # TODO: refactor how arguments is used in a more argparse way.
    arguments = sys.argv[1:]

    # Add the analysis plugin options.
    if u'--analysis' in arguments:
      argument_index = arguments.index(u'--analysis') + 1

      # Get the names of the analysis plugins that should be loaded.
      if len(arguments) > argument_index:
        plugin_names = arguments[argument_index]
      else:
        plugin_names = u'list'

      if plugin_names == u'list':
        self.list_analysis_plugins = True
      else:
        try:
          self.AddAnalysisPluginOptions(analysis_group, plugin_names)
        except errors.BadConfigOption as exception:
          logging.error(u'{0:s}'.format(exception))
          self._output_writer.Write(u'\n')
          self._output_writer.Write(argument_parser.format_usage())
          return False

    try:
      # TODO: refactor how arguments is used in a more argparse way.
      options = argument_parser.parse_args(args=arguments)
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
      self._output_writer.Write(u'ERROR: {0!s}'.format(exception))
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
    self._ParseLanguageOptions(options)
    self._ParseTimezoneOption(options)

    if (self.list_analysis_plugins or self.list_language_identifiers or
        self.list_output_modules or self.list_timezones):
      return

    self._ParseInformationalOptions(options)
    self._ParseDataLocationOption(options)
    self._ParseLogFileOptions(options)

    self._ParseAnalysisPluginOptions(options)
    self._ParseProcessingOptions(options)
    self._ParseFilterOptions(options)

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

    self._ParseStorageFileOptions(options)
    # TODO: move check into _CheckStorageFile.
    if not self._storage_file_path:
      raise errors.BadConfigOption(u'Missing storage file option.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          u'No such storage file: {0:s}.'.format(self._storage_file_path))

    self._ParseOutputModuleOptions(
        options, self._knowledge_base,
        preferred_language=self._preferred_language,
        preferred_time_zone=self._preferred_time_zone)

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

    storage_reader = storage_zip_file.ZIPStorageFileReader(
        self._storage_file_path)
    self._number_of_analysis_reports = (
        storage_reader.GetNumberOfAnalysisReports())
    storage_reader.Close()

    configuration = configurations.ProcessingConfiguration()
    configuration.data_location = self._data_location

    analysis_counter = None
    if self._analysis_plugins:
      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, self._storage_file_path)

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
      storage_reader = storage_zip_file.ZIPStorageFileReader(
          self._storage_file_path)

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
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=u'Analysis reports generated')
      for element, count in analysis_counter.most_common():
        if element != u'total':
          table_view.AddRow([element, count])

      table_view.AddRow([u'Total', analysis_counter[u'total']])
      table_view.Write(self._output_writer)

    if events_counter:
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=u'Export results')
      for element, count in events_counter.most_common():
        table_view.AddRow([element, count])
      table_view.Write(self._output_writer)

    storage_reader = storage_zip_file.ZIPStorageFileReader(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(storage_reader)
