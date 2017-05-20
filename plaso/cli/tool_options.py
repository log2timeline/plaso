# -*- coding: utf-8 -*-
"""The CLI tool options mix-ins."""

import logging
import os
import sys

from plaso.analysis import manager as analysis_manager
from plaso.cli import views
from plaso.cli import tools
from plaso.cli.helpers import manager as helpers_manager
from plaso.filters import manager as filters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import frontend
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface as output_interface
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.winnt import language_ids

import pytz  # pylint: disable=wrong-import-order


# TODO: pass argument_parser instead of argument_group and add groups
# in mix-ins.


class AnalysisPluginOptions(object):
  """Analysis plugin options mix-in.

  Attributes:
    list_analysis_plugins (bool): True if information about the analysis
        plugins should be shown.
  """

  def __init__(self):
    """Initializes analysis plugin options."""
    super(AnalysisPluginOptions, self).__init__()
    self._analysis_manager = analysis_manager.AnalysisPluginManager
    self._analysis_plugins = None
    self.list_analysis_plugins = False

  def _GetAnalysisPlugins(self, names):
    """Retrieves analysis plugins.

    Args:
      names (str): comma separated names of analysis plugins to enable.

    Returns:
      list[AnalysisPlugin]: analysis plugins.
    """
    if not names:
      return []

    names = [name.strip() for name in names.split(u',')]

    analysis_plugins = self._analysis_manager.GetPluginObjects(names)
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

  def ListAnalysisPlugins(self):
    """Lists the analysis modules."""
    analysis_plugin_info = self._analysis_manager.GetAllPluginInformation()

    column_width = 10
    for name, _, _ in analysis_plugin_info:
      if len(name) > column_width:
        column_width = len(name)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Analysis Plugins')
    # TODO: add support for a 3 column table.
    for name, description, type_string in analysis_plugin_info:
      description = u'{0:s} [{1:s}]'.format(description, type_string)
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)


class FilterOptions(object):
  """Filter options mix-in."""

  _FILTERS_URL = u'https://github.com/log2timeline/plaso/wiki/Filters'

  def __init__(self):
    """Initializes filter options."""
    super(FilterOptions, self).__init__()
    self._event_filter = None
    self._event_filter_expression = None
    self._filters_manager = filters_manager.FiltersManager
    self._time_slice = None
    self._use_time_slicer = False

  def _ParseFilterOptions(self, options):
    """Parses the filter options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._event_filter_expression = self.ParseStringOption(options, u'filter')
    if self._event_filter_expression:
      self._event_filter = self._filters_manager.GetFilterObject(
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


class LanguageOptions(object):
  """Language options mix-in.

  Attributes:
    list_language_identifiers (bool): True if information about the language
        identifiers should be shown.
  """

  def __init__(self):
    """Initializes language options."""
    super(LanguageOptions, self).__init__()
    self._preferred_language = u'en-US'
    self.list_language_identifiers = False

  def _ParseLanguageOptions(self, options):
    """Parses the language options.

    Args:
      options (argparse.Namespace): command line arguments.
    """
    preferred_language = self.ParseStringOption(
        options, u'preferred_language', default_value=u'en-US')

    if preferred_language == u'list':
      self.list_language_identifiers = True
      return

    self._preferred_language = preferred_language

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

  def ListLanguageIdentifiers(self):
    """Lists the language identifiers."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Identifier', u'Language'],
        title=u'Language identifiers')
    for language_id, value_list in sorted(
        language_ids.LANGUAGE_IDENTIFIERS.items()):
      table_view.AddRow([language_id, value_list[1]])
    table_view.Write(self._output_writer)


class OutputModuleOptions(object):
  """Output module options mix-in.

  Attributes:
    list_output_modules (bool): True if information about the output modules
        should be shown.
  """

  def __init__(self):
    """Initializes output module options."""
    super(OutputModuleOptions, self).__init__()
    self._output_filename = None
    self._output_format = None
    self._output_manager = output_manager.OutputManager
    self._output_module = None
    self.list_output_modules = False

  def _GetOutputModulesInformation(self):
    """Retrieves the output modules information.

    Returns:
      list[tuple[str, str]]: pairs of output module names and descriptions.
    """
    output_modules_information = []
    for name, output_class in self._output_manager.GetOutputClasses():
      output_modules_information.append((name, output_class.DESCRIPTION))

    return output_modules_information

  def _ParseOutputModuleOptions(
      self, options, knowledge_base, preferred_language=u'en-US',
      preferred_time_zone=u'UTC'):
    """Parses the output module options.

    Args:
      options (argparse.Namespace): command line arguments.
      knowledge_base (KnowledgeBase): knowledge base.
      preferred_language (Optional[str]): preferred language.
      preferred_time_zone (Optional[str]): preferred time zone.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    output_format = getattr(options, u'output_format', u'dynamic')

    if output_format == u'list':
      self.list_output_modules = True
      return

    if not output_format:
      raise errors.BadConfigOption(u'Missing output format.')

    if not self._output_manager.HasOutputClass(output_format):
      raise errors.BadConfigOption(
          u'Unsupported output format: {0:s}.'.format(output_format))

    self._output_format = output_format
    self._output_filename = getattr(options, u'write', None)

    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._data_location)

    try:
      formatter_mediator.SetPreferredLanguageIdentifier(preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    mediator = output_mediator.OutputMediator(
        knowledge_base, formatter_mediator,
        preferred_encoding=self.preferred_encoding)
    mediator.SetTimezone(preferred_time_zone)

    try:
      self._output_module = self._output_manager.NewOutputModule(
          output_format, mediator)

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
                output_format))

      if os.path.exists(self._output_filename):
        raise errors.BadConfigOption(
            u'Output file already exists: {0:s}.'.format(self._output_filename))

      output_file_object = open(self._output_filename, u'wb')
      output_writer = tools.FileObjectOutputWriter(output_file_object)

      self._output_module.SetOutputWriter(output_writer)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self._output_module)

    # Check if there are parameters that have not been defined and need to
    # in order for the output module to continue. Prompt user to supply
    # those that may be missing.
    missing_parameters = self._output_module.GetMissingArguments()
    while missing_parameters:
      for parameter in missing_parameters:
        value = self._PromptUserForInput(
            u'Missing parameter {0:s} for output module'.format(parameter))
        if value is None:
          logging.warning(
              u'Unable to set the missing parameter for: {0:s}'.format(
                  parameter))
          continue

        setattr(options, parameter, value)

      helpers_manager.ArgumentHelperManager.ParseOptions(
          options, self._output_module)
      missing_parameters = self._output_module.GetMissingArguments()

  def AddOutputModuleOptions(self, argument_group):
    """Adds the output module options to the argument group

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'-o', u'--output_format', u'--output-format', metavar=u'FORMAT',
        dest=u'output_format', default=u'dynamic', help=(
            u'The output format. Use "-o list" to see a list of available '
            u'output formats.'))

    argument_group.add_argument(
        u'-w', u'--write', metavar=u'OUTPUT_FILE', dest=u'write',
        help=u'Output filename.')

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
      output_format = arguments[argument_index]
    else:
      output_format = u'dynamic'

    if output_format == u'list':
      return

    module_names = output_format.split(u',')
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, argument_category=u'output', module_list=module_names)

  def ListOutputModules(self):
    """Lists the output modules."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Output Modules')

    for name, output_class in self._output_manager.GetOutputClasses():
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = list(self._output_manager.GetDisabledOutputClasses())
    if not disabled_classes:
      return

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Disabled Output Modules')
    for name, output_class in disabled_classes:
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)


class StorageFileOptions(object):
  """Storage file options mix-in."""

  def __init__(self):
    """Initializes storage file options."""
    super(StorageFileOptions, self).__init__()
    self._storage_file_path = None

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

  def _ParseStorageFileOptions(self, options):
    """Parses the storage file options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._storage_file_path = self.ParseStringOption(options, u'storage_file')

  def AddStorageFileOptions(self, argument_group):
    """Adds the storage file options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        u'storage_file', metavar=u'STORAGE_FILE', nargs=u'?', type=str,
        default=None, help=u'The path of the storage file.')
