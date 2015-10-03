#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Psort (Plaso Síar Og Raðar Þessu) - Makes output from Plaso Storage files.

Sample Usage:
  psort.py /tmp/mystorage.dump "date > '01-06-2012'"

See additional details here: http://plaso.kiddaland.net/usage/psort
"""

import argparse
import multiprocessing
import logging
import pdb
import sys
import time

# The following import makes sure the filters are registered.
from plaso import filters  # pylint: disable=unused-import
from plaso.cli import analysis_tool
from plaso.cli import tools as cli_tools
from plaso.cli import views as cli_views
from plaso.cli.helpers import manager as helpers_manager
from plaso.filters import manager as filters_manager
from plaso.frontend import psort
from plaso.output import interface as output_interface
from plaso.output import manager as output_manager
from plaso.lib import errors
from plaso.winnt import language_ids


class PsortOptions(object):
  """Class to define psort options."""


class PsortTool(analysis_tool.AnalysisTool):
  """Class that implements the psort CLI tool."""

  _URL = u'http://plaso.kiddaland.net/usage/filters'

  NAME = u'psort'
  DESCRIPTION = (
      u'Application to read, filter and process output from a plaso storage '
      u'file.')

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: the input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(PsortTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._analysis_plugins = None
    self._analysis_plugins_output_format = None
    self._deduplicate_events = True
    self._filter_expression = None
    self._filter_object = None
    self._front_end = psort.PsortFrontend()
    self._options = None
    self._output_format = None
    self._time_slice_event_time_string = None
    self._time_slice_duration = 5
    self._use_time_slicer = False

    self.list_analysis_plugins = False
    self.list_language_identifiers = False
    self.list_output_modules = False

  def _ParseAnalysisPluginOptions(self, options):
    """Parses the analysis plugin options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
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
          u'Non-existing analysis plugins specified: {0:s}'.format(
              u' '.join(difference)))

    self._analysis_plugins = analysis_plugin_string

  def _ParseExperimentalOptions(self, options):
    """Parses the experimental plugin options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    use_zeromq = getattr(options, u'use_zeromq', False)
    if use_zeromq:
      self._front_end.SetUseZeroMQ(use_zeromq)

  def _ParseFilterOptions(self, options):
    """Parses the filter options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._filter_expression = self.ParseStringOption(options, u'filter')
    if self._filter_expression:
      self._filter_object = filters_manager.FiltersManager.GetFilterObject(
          self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

    self._time_slice_event_time_string = getattr(options, u'slice', None)
    self._time_slice_duration = getattr(options, u'slice_size', 5)
    self._use_time_slicer = getattr(options, u'slicer', False)

    self._front_end.SetFilter(self._filter_object, self._filter_expression)

    # The slice and slicer cannot be set at the same time.
    if self._time_slice_event_time_string and self._use_time_slicer:
      raise errors.BadConfigOption(
          u'Time slice and slicer cannot be used at the same time.')

  def _ParseInformationalOptions(self, options):
    """Parses the informational options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PsortTool, self)._ParseInformationalOptions(options)

    self._quiet_mode = getattr(options, u'quiet', False)
    self._front_end.SetQuietMode(self._quiet_mode)

  def _ParseLanguageOptions(self, options):
    """Parses the language options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    preferred_language = self.ParseStringOption(options, u'preferred_language')
    if not preferred_language:
      preferred_language = u'en-US'

    if preferred_language == u'list':
      self.list_language_identifiers = True
    else:
      self._front_end.SetPreferredLanguageIdentifier(preferred_language)

  def _ProcessStorage(self):
    """Processes a plaso storage file.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    time_slice = None
    if self._time_slice_event_time_string is not None or self._use_time_slicer:
      time_slice = self._front_end.GetTimeSlice(
          self._time_slice_event_time_string,
          duration=self._time_slice_duration, timezone=self._timezone)

    if self._analysis_plugins:
      read_only = False
    else:
      read_only = True

    try:
      storage_file = self._front_end.OpenStorage(
          self._storage_file_path, read_only=read_only)
    except IOError as exception:
      raise RuntimeError(
          u'Unable to open storage file: {0:s} with error: {1:s}.'.format(
              self._storage_file_path, exception))

    output_module = self._front_end.GetOutputModule(
        storage_file, preferred_encoding=self.preferred_encoding,
        timezone=self._timezone)

    if isinstance(output_module, output_interface.LinearOutputModule):
      if self._output_filename:
        output_file_object = open(self._output_filename, u'wb')
        output_writer = cli_tools.FileObjectOutputWriter(output_file_object)
      else:
        output_writer = cli_tools.StdoutOutputWriter()
      output_module.SetOutputWriter(output_writer)

    # TODO: To set the filter we need to have the filter object. This may
    # be better handled in an argument helper, but ATM the argument helper
    # does not have access to the actual filter object.
    if hasattr(output_module, u'SetFieldsFilter') and self._filter_object:
      output_module.SetFieldsFilter(self._filter_object)

    try:
      helpers_manager.ArgumentHelperManager.ParseOptions(
          self._options, output_module)
    except errors.BadConfigOption as exception:
      raise RuntimeError(exception)

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

    # Get ANALYSIS PLUGINS AND CONFIGURE!
    get_plugins_and_producers = self._front_end.GetAnalysisPluginsAndEventQueues
    analysis_plugins, event_queue_producers = get_plugins_and_producers(
        self._analysis_plugins)

    for analysis_plugin in analysis_plugins:
      helpers_manager.ArgumentHelperManager.ParseOptions(
          self._options, analysis_plugin)

    counter = self._front_end.ProcessStorage(
        output_module, storage_file, analysis_plugins, event_queue_producers,
        deduplicate_events=self._deduplicate_events,
        preferred_encoding=self.preferred_encoding,
        time_slice=time_slice, use_time_slicer=self._use_time_slicer)

    if not self._quiet_mode:
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=u'Counter')
      for element, count in counter.most_common():
        table_view.AddRow([element, count])
      table_view.Write(self._output_writer)

  def _PromptUserForInput(self, input_text):
    """Prompts user for an input and return back read data.

    Args:
      input_text: the text used for prompting the user for input.

    Returns:
      string containing the input read from the user.
    """
    self._output_writer.Write(u'{0:s}: '.format(input_text))
    return self._input_reader.Read()

  def AddAnalysisPluginOptions(self, argument_group, plugin_names):
    """Adds the analysis plugin options to the argument group

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
      plugin_names: a string containing comma separated analysis plugin names.

    Raises:
      BadConfigOption: if non-existing analysis plugin names are specified.
    """
    if plugin_names == u'list':
      return

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, u'analysis')

  def AddExperimentalOptions(self, argument_group):
    """Adds experimental options to the argument group

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--use_zeromq', action=u'store_true', dest=u'use_zeromq', help=(
            u'Enables experimental queueing using ZeroMQ'))

  def AddFilterOptions(self, argument_group):
    """Adds the filter options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--slice', metavar=u'DATE', dest=u'slice', type=str,
        default=u'', action=u'store', help=(
            u'Create a time slice around a certain date. This parameter, if '
            u'defined will display all events that happened X minutes before '
            u'and after the defined date. X is controlled by the parameter '
            u'--slice_size but defaults to 5 minutes.'))

    argument_group.add_argument(
        u'--slice_size', dest=u'slice_size', type=int, default=5,
        action=u'store', help=(
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
            u'and how to use them can be found here: {0:s}').format(self._URL))

  def AddLanguageOptions(self, argument_group):
    """Adds the language options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
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
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
      module_names: a list of output module names.
    """
    if u'list' in module_names:
      return

    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, argument_category=u'output', module_list=module_names)

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
    for name, output_class in sorted(self._front_end.GetOutputClasses()):
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = output_manager.OutputManager.GetDisabledOutputClasses()
    if not disabled_classes:
      return

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Disabled Output Modules')
    for output_class in disabled_classes:
      table_view.AddRow([output_class.NAME, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      A boolean value indicating the arguments were successfully parsed.
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

    experimental_group = argument_parser.add_argument_group(u'Experimental')
    self.AddExperimentalOptions(experimental_group)

    info_group = argument_parser.add_argument_group(u'Informational Arguments')

    self.AddLogFileOptions(info_group)

    self.AddInformationalOptions(info_group)

    filter_group = argument_parser.add_argument_group(u'Filter Arguments')

    self.AddFilterOptions(filter_group)

    input_group = argument_parser.add_argument_group(u'Input Arguments')

    self.AddDataLocationOption(input_group)

    output_group = argument_parser.add_argument_group(u'Output Arguments')

    output_group.add_argument(
        u'-a', u'--include_all', action=u'store_false', dest=u'dedup',
        default=True, help=(
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
        help=u'Output filename, defaults to stdout.')

    self.AddTimezoneOption(output_group)

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
      options: the command line arguments (instance of argparse.Namespace).

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
    self._ParseExperimentalOptions(options)
    self._ParseFilterOptions(options)
    self._front_end.SetStorageFile(self._storage_file_path)

    if self._debug_mode:
      logging_level = logging.DEBUG
    elif self._quiet_mode:
      logging_level = logging.WARNING
    else:
      logging_level = logging.INFO

    log_file = getattr(options, u'log_file', None)
    self._ConfigureLogging(filename=log_file, log_level=logging_level)

    self._output_format = getattr(options, u'output_format', None)
    if not self._output_format:
      raise errors.BadConfigOption(u'Missing output format.')
    self._front_end.SetOutputFormat(self._output_format)

    if not self._front_end.HasOutputClass(self._output_format):
      raise errors.BadConfigOption(
          u'Unsupported output format: {0:s}.'.format(self._output_format))

    self._deduplicate_events = getattr(options, u'dedup', True)

    self._output_filename = getattr(options, u'write', None)
    if self._output_filename:
      self._front_end.SetOutputFilename(self._output_filename)

    if self._data_location:
      self._front_end.SetDataLocation(self._data_location)
      # Update the data location with the calculated value.
      options.data_location = self._data_location
    else:
      logging.warning(u'Unable to automatically determine data location.')

    # TODO: refactor this.
    self._options = options

  def ProcessStorage(self):
    """Processes a plaso storage."""
    try:
      self._ProcessStorage()

    except IOError as exception:
      # Piping results to "|head" for instance causes an IOError.
      if u'Broken pipe' not in exception:
        logging.error(u'Processing stopped early: {0:s}.'.format(exception))

    except KeyboardInterrupt:
      pass

    # Catching every remaining exception in case we are debugging.
    except Exception as exception:
      if not self._debug_mode:
        raise
      logging.error(u'{0:s}'.format(exception))
      pdb.post_mortem()


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

  tool.ProcessStorage()
  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
