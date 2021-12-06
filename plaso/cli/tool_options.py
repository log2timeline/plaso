# -*- coding: utf-8 -*-
"""The CLI tool options mix-ins."""

import os
import pytz

from plaso.analysis import manager as analysis_manager
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.cli.helpers import profiling
from plaso.analyzers.hashers import manager as hashers_manager
from plaso.lib import errors
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator


# TODO: pass argument_parser instead of argument_group and add groups
# in mix-ins.


class AnalysisPluginOptions(object):
  """Analysis plugin options mix-in."""

  # pylint: disable=no-member

  def _CreateAnalysisPlugins(self, options):
    """Creates the analysis plugins.

    Args:
      options (argparse.Namespace): command line arguments.

    Returns:
      dict[str, AnalysisPlugin]: analysis plugins and their names.
    """
    if not self._analysis_plugins:
      return {}

    analysis_plugins = (
        analysis_manager.AnalysisPluginManager.GetPluginObjects(
            self._analysis_plugins))

    for analysis_plugin in analysis_plugins.values():
      helpers_manager.ArgumentHelperManager.ParseOptions(
          options, analysis_plugin)

    return analysis_plugins

  def ListAnalysisPlugins(self):
    """Lists the analysis modules."""
    analysis_plugin_info = (
        analysis_manager.AnalysisPluginManager.GetAllPluginInformation())

    column_width = 10
    for name, _, _ in analysis_plugin_info:
      if len(name) > column_width:
        column_width = len(name)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Analysis Plugins')
    # TODO: add support for a 3 column table.
    for name, description, type_string in analysis_plugin_info:
      description = '{0:s} [{1:s}]'.format(description, type_string)
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)


class HashersOptions(object):
  """Hashers options mix-in."""

  # pylint: disable=no-member

  def __init__(self):
    """Initializes hasher options."""
    super(HashersOptions, self).__init__()
    self._hasher_file_size_limit = None
    self._hasher_names_string = None

  def ListHashers(self):
    """Lists information about the available hashers."""
    hashers_information = hashers_manager.HashersManager.GetHashersInformation()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Hashers')

    for name, description in sorted(hashers_information):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)


class OutputModuleOptions(object):
  """Output module options mix-in.

  Attributes:
    list_time_zones (bool): True if the time zones should be listed.
  """

  # pylint: disable=no-member

  # Output format that have second-only date and time value and/or a limited
  # predefined set of output fields.
  _DEPRECATED_OUTPUT_FORMATS = frozenset(['l2tcsv', 'l2ttln', 'tln'])

  _MESSAGE_FORMATTERS_DIRECTORY_NAME = 'formatters'
  _MESSAGE_FORMATTERS_FILE_NAME = 'formatters.yaml'

  def __init__(self):
    """Initializes output module options."""
    super(OutputModuleOptions, self).__init__()
    self._output_dynamic_time = None
    self._output_filename = None
    self._output_format = None
    self._output_mediator = None
    self._output_module = None
    self._output_time_zone = None

    self.list_time_zones = False

  def _CreateOutputMediator(self):
    """Creates an output mediator.

    Raises:
      BadConfigOption: if the message formatters file or directory cannot be
          read.
    """
    self._output_mediator = output_mediator.OutputMediator(
        self._knowledge_base, data_location=self._data_location,
        dynamic_time=self._output_dynamic_time,
        preferred_encoding=self.preferred_encoding)

    self._output_mediator.SetTimeZone(self._output_time_zone)

    self._ReadMessageFormatters()

  def _CreateOutputModule(self, options):
    """Creates an output module.

    Args:
      options (argparse.Namespace): command line arguments.

    Returns:
      OutputModule: output module.

    Raises:
      BadConfigOption: if parameters are missing.
      RuntimeError: if the output module cannot be created.
    """
    if self._output_format in self._DEPRECATED_OUTPUT_FORMATS:
      self._PrintUserWarning((
          'the output format: {0:s} has significant limitations such as '
          'second-only date and time values and/or a limited predefined '
          'set of output fields. It is strongly recommend to use an '
          'alternative output format like: dynamic.').format(
              self._output_format))

    self._CreateOutputMediator()

    try:
      output_module = output_manager.OutputManager.NewOutputModule(
          self._output_format, self._output_mediator)

    except (KeyError, ValueError) as exception:
      raise RuntimeError(
          'Unable to create output module with error: {0!s}'.format(
              exception))

    if output_module.WRITES_OUTPUT_FILE:
      if not self._output_filename:
        raise errors.BadConfigOption(
            'Output format: {0:s} requires an output file'.format(
                self._output_format))

      if os.path.exists(self._output_filename):
        raise errors.BadConfigOption(
            'Output file already exists: {0:s}.'.format(self._output_filename))

      output_module.Open(path=self._output_filename)
    else:
      output_module.Open()

    helpers_manager.ArgumentHelperManager.ParseOptions(options, output_module)

    # Check if there are parameters that have not been defined and need to
    # in order for the output module to continue. Prompt user to supply
    # those that may be missing.
    missing_parameters = output_module.GetMissingArguments()
    if missing_parameters and self._unattended_mode:
      raise errors.BadConfigOption(
          'Unable to create output module missing parameters: {0:s}'.format(
              ', '.join(missing_parameters)))

    while missing_parameters:
      self._PromptUserForMissingOutputModuleParameters(
          options, missing_parameters)

      helpers_manager.ArgumentHelperManager.ParseOptions(options, output_module)
      missing_parameters = output_module.GetMissingArguments()

    return output_module

  def _GetOutputModulesInformation(self):
    """Retrieves the output modules information.

    Returns:
      list[tuple[str, str]]: pairs of output module names and descriptions.
    """
    output_modules_information = []
    for name, output_class in output_manager.OutputManager.GetOutputClasses():
      output_modules_information.append((name, output_class.DESCRIPTION))

    return output_modules_information

  def _ParseOutputOptions(self, options):
    """Parses the output options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._output_dynamic_time = getattr(options, 'dynamic_time', False)

    time_zone_string = self.ParseStringOption(options, 'output_time_zone')
    if isinstance(time_zone_string, str):
      if time_zone_string.lower() == 'list':
        self.list_time_zones = True

      elif time_zone_string:
        try:
          pytz.timezone(time_zone_string)
        except pytz.UnknownTimeZoneError:
          raise errors.BadConfigOption(
              'Unknown time zone: {0:s}'.format(time_zone_string))

        self._output_time_zone = time_zone_string

  def _PromptUserForMissingOutputModuleParameters(
      self, options, missing_parameters):
    """Prompts the user for missing output module parameters.

    Args:
      options (argparse.Namespace): command line arguments.
      missing_parameters (list[str]): names of missing output module parameters.
    """
    for parameter in missing_parameters:
      value = None
      while not value:
        value = self._PromptUserForInput(
            'Please specific a value for {0:s}'.format(parameter))

      setattr(options, parameter, value)

  def _ReadMessageFormatters(self):
    """Reads the message formatters from a formatters file or directory.

    Raises:
      BadConfigOption: if the message formatters file or directory cannot be
          read.
    """
    formatters_directory = os.path.join(
        self._data_location, self._MESSAGE_FORMATTERS_DIRECTORY_NAME)
    formatters_file = os.path.join(
        self._data_location, self._MESSAGE_FORMATTERS_FILE_NAME)

    if os.path.isdir(formatters_directory):
      try:
        self._output_mediator.ReadMessageFormattersFromDirectory(
            formatters_directory)
      except KeyError as exception:
        raise errors.BadConfigOption((
            'Unable to read message formatters from directory: {0:s} with '
            'error: {1!s}').format(formatters_directory, exception))

    elif os.path.isfile(formatters_file):
      try:
        self._output_mediator.ReadMessageFormattersFromFile(
            formatters_file)
      except KeyError as exception:
        raise errors.BadConfigOption((
            'Unable to read message formatters from file: {0:s} with error: '
            '{1!s}').format(formatters_file, exception))

    else:
      raise errors.BadConfigOption('Missing formatters file and directory.')

  def AddOutputOptions(self, argument_group):
    """Adds the output options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    argument_group.add_argument(
        '--dynamic_time', '--dynamic-time', dest='dynamic_time',
        action='store_true', default=False, help=(
            'Indicate that the output should use dynamic time.'))

    # Note the default here is None so we can determine if the time zone
    # option was set.
    argument_group.add_argument(
        '--output_time_zone', '--output-time-zone', dest='output_time_zone',
        action='store', metavar='TIME_ZONE', type=str, default=None, help=(
            'time zone of date and time values written to the output, if '
            'supported by the output format. Output formats that support '
            'this are: dynamic and l2t_csv. Use "list" to see a list of '
            'available time zones.'))

  def ListOutputModules(self):
    """Lists the output modules."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Output Modules')

    output_classes = sorted(
        output_manager.OutputManager.GetOutputClasses())
    for name, output_class in output_classes:
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = sorted(
        output_manager.OutputManager.GetDisabledOutputClasses())
    if not disabled_classes:
      return

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Disabled Output Modules')
    for name, output_class in disabled_classes:
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)


class ProfilingOptions(object):
  """Profiling options mix-in."""

  # pylint: disable=no-member

  def __init__(self):
    """Initializes profiling options."""
    super(ProfilingOptions, self).__init__()
    self._profilers = set()
    self._profiling_directory = None
    self._profiling_sample_rate = (
        profiling.ProfilingArgumentsHelper.DEFAULT_PROFILING_SAMPLE_RATE)

  def ListProfilers(self):
    """Lists information about the available profilers."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Profilers')

    profilers_information = sorted(
        profiling.ProfilingArgumentsHelper.PROFILERS_INFORMATION.items())
    for name, description in profilers_information:
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)


class StorageFileOptions(object):
  """Storage file options mix-in."""

  def AddStorageOptions(self, argument_parser):
    """Adds the storage options to the argument group.

    Args:
      argument_parser (argparse.ArgumentParser): argparse argument parser.
    """
    argument_parser.add_argument(
        'storage_file', metavar='PATH', nargs='?', type=str, default=None,
        help='Path to a storage file.')
