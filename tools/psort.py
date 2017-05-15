#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Psort (Plaso Síar Og Raðar Þessu) - Makes output from Plaso Storage files.

Sample Usage:
  psort.py /tmp/mystorage.dump "date > '01-06-2012'"

See additional details here:
  https://github.com/log2timeline/plaso/wiki/Using-psort
"""

import argparse
import collections
import multiprocessing
import logging
import os
import sys
import time

try:
  import win32console
except ImportError:
  win32console = None

import plaso
# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import
from plaso.cli import analysis_tool
from plaso.cli import tools as cli_tools
from plaso.cli import views as cli_views
from plaso.cli.helpers import manager as helpers_manager
from plaso.filters import manager as filters_manager
from plaso.frontend import frontend
from plaso.frontend import psort
from plaso.engine import configurations
from plaso.output import interface as output_interface
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.winnt import language_ids

import pytz  # pylint: disable=wrong-import-order


class PsortOptions(object):
  """Class to define psort options."""


class PsortTool(analysis_tool.AnalysisTool):
  """Class that implements the psort CLI tool."""

  _FILTERS_URL = u'https://github.com/log2timeline/plaso/wiki/Filters'

  NAME = u'psort'
  DESCRIPTION = (
      u'Application to read, filter and process output from a plaso storage '
      u'file.')

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
    self._analysis_plugins = None
    self._analysis_plugins_output_format = None
    self._command_line_arguments = None
    self._deduplicate_events = True
    self._event_filter = None
    self._event_filter_expression = None
    self._front_end = psort.PsortFrontend()
    self._number_of_analysis_reports = 0
    self._options = None
    self._output_filename = None
    self._output_format = None
    self._status_view_mode = u'linear'
    self._stdout_output_writer = isinstance(
        self._output_writer, cli_tools.StdoutOutputWriter)
    self._temporary_directory = None
    self._time_slice = None
    self._use_time_slicer = False
    self._worker_memory_limit = None

    self.list_analysis_plugins = False
    self.list_language_identifiers = False
    self.list_output_modules = False

  def _FormatStatusTableRow(self, process_status):
    """Formats a status table row.

    Args:
      process_status (ProcessStatus): processing status.
    """
    # This check makes sure the columns are tab aligned.
    identifier = process_status.identifier
    if len(identifier) < 8:
      identifier = u'{0:s}\t\t'.format(identifier)
    elif len(identifier) < 16:
      identifier = u'{0:s}\t'.format(identifier)

    status = process_status.status
    if len(status) < 8:
      status = u'{0:s}\t'.format(status)

    events = u''
    if (process_status.number_of_consumed_events is not None and
        process_status.number_of_consumed_events_delta is not None):
      events = u'{0:d} ({1:d})'.format(
          process_status.number_of_consumed_events,
          process_status.number_of_consumed_events_delta)

    # This check makes sure the columns are tab aligned.
    if len(events) < 8:
      events = u'{0:s}\t'.format(events)

    event_tags = u''
    if (process_status.number_of_produced_event_tags is not None and
        process_status.number_of_produced_event_tags_delta is not None):
      event_tags = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_event_tags,
          process_status.number_of_produced_event_tags_delta)

    # This check makes sure the columns are tab aligned.
    if len(event_tags) < 8:
      event_tags = u'{0:s}\t'.format(event_tags)

    reports = u''
    if (process_status.number_of_produced_reports is not None and
        process_status.number_of_produced_reports_delta is not None):
      reports = u'{0:d} ({1:d})'.format(
          process_status.number_of_produced_reports,
          process_status.number_of_produced_reports_delta)

    # This check makes sure the columns are tab aligned.
    if len(reports) < 8:
      reports = u'{0:s}\t'.format(reports)

    # TODO: shorten display name to fit in 80 chars and show the filename.
    return u'{0:s}\t{1:d}\t{2:s}\t{3:s}\t{4:s}\t{5:s}'.format(
        identifier, process_status.pid, status, events, event_tags, reports)

  def _ParseAnalysisPluginOptions(self, options):
    """Parses the analysis plugin options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    # Get a list of all available plugins.
    analysis_plugin_info = self._front_end.GetAnalysisPluginInfo()
    analysis_plugin_names = set([
        name.lower() for name, _, _ in analysis_plugin_info])

    analysis_plugin_string = self.ParseStringOption(
        options, u'analysis_plugins')
    if not analysis_plugin_string:
      return

    requested_plugin_names = set([
        name.strip().lower() for name in analysis_plugin_string.split(u',')])

    # Check to see if we are trying to load plugins that do not exist.
    difference = requested_plugin_names.difference(analysis_plugin_names)
    if difference:
      raise errors.BadConfigOption(
          u'Non-existent analysis plugins specified: {0:s}'.format(
              u' '.join(difference)))

    self._analysis_plugins = analysis_plugin_string


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

    self._front_end.SetEventFilter(
        self._event_filter, self._event_filter_expression)

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
      self._time_slice = frontend.TimeSlice(
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
    self._front_end.SetQuietMode(self._quiet_mode)

    self._status_view_mode = getattr(options, u'status_view_mode', u'linear')

  def _ParseLanguageOptions(self, options):
    """Parses the language options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    preferred_language = self.ParseStringOption(
        options, u'preferred_language', default_value=u'en-US')

    if preferred_language == u'list':
      self.list_language_identifiers = True
    else:
      self._front_end.SetPreferredLanguageIdentifier(preferred_language)

  def _ParseProcessingOptions(self, options):
    """Parses the processing options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    use_zeromq = getattr(options, u'use_zeromq', True)
    self._front_end.SetUseZeroMQ(use_zeromq)

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
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

  def _PrintStatusHeader(self):
    """Prints the processing status header."""
    self._output_writer.Write(
        u'Storage file\t: {0:s}\n'.format(self._storage_file_path))

    self._output_writer.Write(u'\n')

  def _PrintStatusUpdate(self, processing_status):
    """Prints the processing status.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    if self._stdout_output_writer:
      self._ClearScreen()

    output_text = u'plaso - {0:s} version {1:s}\n\n'.format(
        self.NAME, plaso.__version__)
    self._output_writer.Write(output_text)

    self._PrintStatusHeader()

    # TODO: for win32console get current color and set intensity,
    # write the header separately then reset intensity.
    status_header = u'Identifier\t\tPID\tStatus\t\tEvents\t\tTags\t\tReports'
    if not win32console:
      status_header = u'\x1b[1m{0:s}\x1b[0m'.format(status_header)

    status_table = [status_header]

    status_row = self._FormatStatusTableRow(processing_status.foreman_status)
    status_table.append(status_row)

    for worker_status in processing_status.workers_status:
      status_row = self._FormatStatusTableRow(worker_status)
      status_table.append(status_row)

    status_table.append(u'')
    self._output_writer.Write(u'\n'.join(status_table))
    self._output_writer.Write(u'\n')

    if processing_status.aborted:
      self._output_writer.Write(
          u'Processing aborted - waiting for clean up.\n\n')

    # TODO: remove update flicker. For win32console we could set the cursor
    # top left, write the table, clean the remainder of the screen buffer
    # and set the cursor at the end of the table.
    if self._stdout_output_writer:
      # We need to explicitly flush stdout to prevent partial status updates.
      sys.stdout.flush()

  def _PrintStatusUpdateStream(self, processing_status):
    """Prints the processing status as a stream of output.

    Args:
      processing_status (ProcessingStatus): processing status.
    """
    for worker_status in processing_status.workers_status:
      status_line = (
          u'{0:s} (PID: {1:d}) - events consumed: {2:d} - running: '
          u'{3!s}\n').format(
              worker_status.identifier, worker_status.pid,
              worker_status.number_of_consumed_events,
              worker_status.status not in definitions.PROCESSING_ERROR_STATUS)
      self._output_writer.Write(status_line)

  def _PromptUserForInput(self, input_text):
    """Prompts user for an input and return back read data.

    Args:
      input_text (str): text used for prompting the user for input.

    Returns:
      str: input read from the user.
    """
    self._output_writer.Write(u'{0:s}: '.format(input_text))
    return self._input_reader.Read()

  def AddAnalysisPluginOptions(self, argument_group, plugin_names):
    """Adds the analysis plugin options to the argument group

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
      plugin_names (str): comma separated analysis plugin names.

    Raises:
      BadConfigOption: if non-existing analysis plugin names are specified.
    """
    if plugin_names == u'list':
      return

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, u'analysis')

  def AddFilterOptions(self, argument_group):
    """Adds the filter options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--slice', metavar=u'DATE', dest=u'slice', type=str,
        default=u'', action=u'store', help=(
            u'Create a time slice around a certain date. This parameter, if '
            u'defined will display all events that happened X minutes before '
            u'and after the defined date. X is controlled by the parameter '
            u'--slice_size but defaults to 5 minutes.'))

    argument_group.add_argument(
        u'--slice_size', u'--slice-size', dest=u'slice_size', type=int,
        default=5, action=u'store', help=(
            u'Defines the slice size. In the case of a regular time slice it '
            u'defines the number of minutes the slice size should be. In the '
            u'case of the --slicer it determines the number of events before '
            u'and after a filter match has been made that will be included in '
            u'the result set. The default value is 5]. See --slice or --slicer '
            u'for more details about this option.'))

    argument_group.add_argument(
        u'--slicer', dest=u'slicer', action=u'store_true', default=False, help=(
            u'Create a time slice around every filter match. This parameter, '
            u'if defined will save all X events before and after a filter '
            u'match has been made. X is defined by the --slice_size '
            u'parameter.'))

    argument_group.add_argument(
        u'filter', nargs=u'?', action=u'store', metavar=u'FILTER', default=None,
        type=str, help=(
            u'A filter that can be used to filter the dataset before it '
            u'is written into storage. More information about the filters '
            u'and how to use them can be found here: {0:s}').format(
                self._FILTERS_URL))

  def AddLanguageOptions(self, argument_group):
    """Adds the language options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'--language', metavar=u'LANGUAGE', dest=u'preferred_language',
        default=u'en-US', type=str, help=(
            u'The preferred language identifier for Windows Event Log message '
            u'strings. Use "--language list" to see a list of available '
            u'language identifiers. Note that formatting will fall back on '
            u'en-US (LCID 0x0409) if the preferred language is not available '
            u'in the database of message string templates.'))

  # TODO: improve the description of module_names.
  def AddOutputModuleOptions(self, argument_group, module_names):
    """Adds the output module options to the argument group

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
      module_names (list[str]): output module names.
    """
    if u'list' in module_names:
      return

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, argument_category=u'output', module_list=module_names)

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

  def ListAnalysisPlugins(self):
    """Lists the analysis modules."""
    analysis_plugin_info = self._front_end.GetAnalysisPluginInfo()

    column_width = 10
    for name, _, _ in analysis_plugin_info:
      if len(name) > column_width:
        column_width = len(name)

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Analysis Plugins')
    # TODO: add support for a 3 column table.
    for name, description, type_string in analysis_plugin_info:
      description = u'{0:s} [{1:s}]'.format(description, type_string)
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ListLanguageIdentifiers(self):
    """Lists the language identifiers."""
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Identifier', u'Language'],
        title=u'Language identifiers')
    for language_id, value_list in sorted(
        language_ids.LANGUAGE_IDENTIFIERS.items()):
      table_view.AddRow([language_id, value_list[1]])
    table_view.Write(self._output_writer)

  def ListOutputModules(self):
    """Lists the output modules."""
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Output Modules')
    for name, output_class in self._front_end.GetOutputClasses():
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = list(self._front_end.GetDisabledOutputClasses())
    if not disabled_classes:
      return

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Disabled Output Modules')
    for name, output_class in disabled_classes:
      table_view.AddRow([name, output_class.DESCRIPTION])
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

    # The window status-view mode has an annoying flicker on Windows,
    # hence we default to linear status-view mode instead.
    if sys.platform.startswith(u'win'):
      default_status_view = u'linear'
    else:
      default_status_view = u'window'

    info_group.add_argument(
        u'--status_view', u'--status-view', dest=u'status_view_mode',
        choices=[u'linear', u'none', u'window'], action=u'store',
        metavar=u'TYPE', default=default_status_view, help=(
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

    output_group.add_argument(
        u'-o', u'--output_format', u'--output-format', metavar=u'FORMAT',
        dest=u'output_format', default=u'dynamic', help=(
            u'The output format. Use "-o list" to see a list of available '
            u'output formats.'))

    output_group.add_argument(
        u'-w', u'--write', metavar=u'OUTPUTFILE', dest=u'write',
        help=u'Output filename.')

    self.AddTimeZoneOption(output_group)

    # TODO: refactor how arguments is used in a more argparse way.
    arguments = sys.argv[1:]

    # Add the output module options.
    if u'-o' in arguments:
      argument_index = arguments.index(u'-o') + 1
    elif u'--output_format' in arguments:
      argument_index = arguments.index(u'--output_format') + 1
    elif u'--output-format' in arguments:
      argument_index = arguments.index(u'--output-format') + 1
    else:
      argument_index = 0

    if argument_index > 0:
      module_names_string = arguments[argument_index]
      if module_names_string == u'list':
        self.list_output_modules = True
      else:
        module_names = module_names_string.split(u',')
        module_group = argument_parser.add_argument_group(
            u'Output Module Specific Arguments')
        self.AddOutputModuleOptions(module_group, module_names)

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
      logging.error(u'{0:s}'.format(exception))

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

    super(PsortTool, self).ParseOptions(options)
    self._ParseDataLocationOption(options)
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

    self.ParseLogFileOptions(options)
    self._ConfigureLogging(
        filename=self._log_file, format_string=format_string,
        log_level=logging_level)

    self._deduplicate_events = getattr(options, u'dedup', True)

    self._output_filename = getattr(options, u'write', None)

    self._output_format = getattr(options, u'output_format', None)
    if not self._output_format:
      raise errors.BadConfigOption(u'Missing output format.')

    if not self._front_end.HasOutputClass(self._output_format):
      raise errors.BadConfigOption(
          u'Unsupported output format: {0:s}.'.format(self._output_format))

    if self._data_location:
      self._front_end.SetDataLocation(self._data_location)
      # Update the data location with the calculated value.
      options.data_location = self._data_location
    else:
      logging.warning(u'Unable to automatically determine data location.')

    self._command_line_arguments = self.GetCommandLineArguments()

    # TODO: refactor this.
    self._options = options

  def ProcessStorage(self):
    """Processes a plaso storage file.

    Raises:
      BadConfigOption: when a configuration parameter fails validation.
      RuntimeError: if a non-recoverable situation is encountered.
    """
    preferred_time_zone = self._preferred_time_zone or u'UTC'
    output_module = self._front_end.CreateOutputModule(
        self._output_format, preferred_encoding=self.preferred_encoding,
        timezone=preferred_time_zone)

    if isinstance(output_module, output_interface.LinearOutputModule):
      if not self._output_filename:
        raise errors.BadConfigOption((
            u'Output format: {0:s} requires an output file').format(
                self._output_format))

      if self._output_filename and os.path.exists(self._output_filename):
        raise errors.BadConfigOption((
            u'Output file already exists: {0:s}. Aborting.').format(
                self._output_filename))

      output_file_object = open(self._output_filename, u'wb')
      output_writer = cli_tools.FileObjectOutputWriter(output_file_object)

      output_module.SetOutputWriter(output_writer)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        self._options, output_module)

    # Check if there are parameters that have not been defined and need to
    # in order for the output module to continue. Prompt user to supply
    # those that may be missing.
    missing_parameters = output_module.GetMissingArguments()
    while missing_parameters:
      # TODO: refactor this.
      configuration_object = PsortOptions()
      setattr(configuration_object, u'output_format', output_module.NAME)
      for parameter in missing_parameters:
        value = self._PromptUserForInput(
            u'Missing parameter {0:s} for output module'.format(parameter))
        if value is None:
          logging.warning(
              u'Unable to set the missing parameter for: {0:s}'.format(
                  parameter))
          continue

        setattr(configuration_object, parameter, value)

      helpers_manager.ArgumentHelperManager.ParseOptions(
          configuration_object, output_module)
      missing_parameters = output_module.GetMissingArguments()

    analysis_plugins = self._front_end.GetAnalysisPlugins(
        self._analysis_plugins)
    for analysis_plugin in analysis_plugins:
      helpers_manager.ArgumentHelperManager.ParseOptions(
          self._options, analysis_plugin)

    if self._status_view_mode == u'linear':
      status_update_callback = self._PrintStatusUpdateStream
    elif self._status_view_mode == u'window':
      status_update_callback = self._PrintStatusUpdate
    else:
      status_update_callback = None

    session = self._front_end.CreateSession(
        command_line_arguments=self._command_line_arguments,
        preferred_encoding=self.preferred_encoding)

    storage_reader = self._front_end.CreateStorageReader(
        self._storage_file_path)
    self._number_of_analysis_reports = (
        storage_reader.GetNumberOfAnalysisReports())
    storage_reader.Close()

    configuration = configurations.ProcessingConfiguration()
    configuration.data_location = self._options.data_location

    if analysis_plugins:
      storage_writer = self._front_end.CreateStorageWriter(
          session, self._storage_file_path)
      # TODO: handle errors.BadConfigOption

      self._front_end.AnalyzeEvents(
          storage_writer, analysis_plugins, configuration,
          status_update_callback=status_update_callback)

    counter = collections.Counter()
    if self._output_format != u'null':
      storage_reader = self._front_end.CreateStorageReader(
          self._storage_file_path)

      events_counter = self._front_end.ExportEvents(
          storage_reader, output_module, configuration,
          deduplicate_events=self._deduplicate_events,
          status_update_callback=status_update_callback,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

      counter += events_counter

    for item, value in iter(session.analysis_reports_counter.items()):
      counter[item] = value

    if self._quiet_mode:
      return

    self._output_writer.Write(u'Processing completed.\n')

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Counter')
    for element, count in counter.most_common():
      if not element:
        element = u'N/A'
      table_view.AddRow([element, count])
    table_view.Write(self._output_writer)

    storage_reader = self._front_end.CreateStorageReader(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(storage_reader)


def Main():
  """The main function."""
  multiprocessing.freeze_support()

  input_reader = cli_tools.StdinInputReader()
  tool = PsortTool(input_reader=input_reader)

  if not tool.ParseArguments():
    return False

  have_list_option = False
  if tool.list_analysis_plugins:
    tool.ListAnalysisPlugins()
    have_list_option = True

  if tool.list_output_modules:
    tool.ListOutputModules()
    have_list_option = True

  if tool.list_language_identifiers:
    tool.ListLanguageIdentifiers()
    have_list_option = True

  if tool.list_timezones:
    tool.ListTimeZones()
    have_list_option = True

  if have_list_option:
    return True

  try:
    tool.ProcessStorage()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
