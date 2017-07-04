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
from plaso.cli import analysis_tool
from plaso.cli import status_view
from plaso.cli import tools as cli_tools
from plaso.cli import views as cli_views
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import configurations
from plaso.engine import engine
from plaso.engine import knowledge_base
from plaso.filters import manager as filters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import frontend
from plaso.lib import errors
from plaso.lib import timelib
from plaso.multi_processing import psort
from plaso.output import interface as output_interface
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.storage import zip_file as storage_zip_file
from plaso.winnt import language_ids

import pytz  # pylint: disable=wrong-import-order


class PsortOptions(object):
  """Class to define psort options."""


class PsortTool(analysis_tool.AnalysisTool):
  """Class that implements the psort CLI tool."""

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

  _FILTERS_URL = u'https://github.com/log2timeline/plaso/wiki/Filters'

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
    self._event_filter = None
    self._event_filter_expression = None
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._number_of_analysis_reports = 0
    self._output_filename = None
    self._output_format = None
    self._output_module = None
    self._preferred_language = u'en-US'
    self._status_view = status_view.StatusView(self._output_writer, self.NAME)
    self._status_view_mode = self._DEFAULT_STATUS_VIEW_MODE
    self._stdout_output_writer = isinstance(
        self._output_writer, cli_tools.StdoutOutputWriter)
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

    self._status_view_mode = getattr(
        options, u'status_view_mode', self._DEFAULT_STATUS_VIEW_MODE)

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
      self._preferred_language = preferred_language

  def _ParseOutputModuleOptions(self, options):
    """Parses the output module options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    preferred_time_zone = self._preferred_time_zone or u'UTC'

    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._data_location)

    try:
      formatter_mediator.SetPreferredLanguageIdentifier(
          self._preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    output_mediator_object = output_mediator.OutputMediator(
        self._knowledge_base, formatter_mediator,
        preferred_encoding=self.preferred_encoding)
    output_mediator_object.SetTimezone(preferred_time_zone)

    try:
      self._output_module = output_manager.OutputManager.NewOutputModule(
          self._output_format, output_mediator_object)

    except IOError as exception:
      raise RuntimeError(
          u'Unable to create output module with error: {0:s}'.format(
              exception))

    if not self._output_module:
      raise RuntimeError(u'Missing output module.')

    if isinstance(self._output_module, output_interface.LinearOutputModule):
      if not self._output_filename:
        raise errors.BadConfigOption((
            u'Output format: {0:s} requires an output file').format(
                self._output_format))

      if os.path.exists(self._output_filename):
        raise errors.BadConfigOption(
            u'Output file already exists: {0:s}.'.format(self._output_filename))

      output_file_object = open(self._output_filename, u'wb')
      output_writer = cli_tools.FileObjectOutputWriter(output_file_object)

      self._output_module.SetOutputWriter(output_writer)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self._output_module)

    # Check if there are parameters that have not been defined and need to
    # in order for the output module to continue. Prompt user to supply
    # those that may be missing.
    missing_parameters = self._output_module.GetMissingArguments()
    while missing_parameters:
      # TODO: refactor this.
      configuration_object = PsortOptions()
      setattr(configuration_object, u'output_format', self._output_module.NAME)

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
          configuration_object, self._output_module)
      missing_parameters = self._output_module.GetMissingArguments()

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
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow([u'String', analysis_report.GetString()])

      table_view.Write(self._output_writer)

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
    analysis_plugin_info = self._analysis_manager.GetAllPluginInformation()

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

    for name, output_class in output_manager.OutputManager.GetOutputClasses():
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = list(
        output_manager.OutputManager.GetDisabledOutputClasses())
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

    if not output_manager.OutputManager.HasOutputClass(self._output_format):
      raise errors.BadConfigOption(
          u'Unsupported output format: {0:s}.'.format(self._output_format))

    if self._data_location:
      # Update the data location with the calculated value.
      options.data_location = self._data_location
    else:
      logging.warning(u'Unable to automatically determine data location.')

    self._command_line_arguments = self.GetCommandLineArguments()

    self._ParseOutputModuleOptions(options)

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

    counter = collections.Counter()
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

    storage_reader = storage_zip_file.ZIPStorageFileReader(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(storage_reader)
