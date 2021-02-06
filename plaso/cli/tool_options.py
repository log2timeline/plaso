# -*- coding: utf-8 -*-
"""The CLI tool options mix-ins."""

import os

from plaso.analysis import manager as analysis_manager
from plaso.cli import logger
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.cli.helpers import profiling
from plaso.analyzers.hashers import manager as hashers_manager
from plaso.lib import errors
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.winnt import language_ids


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
  """Output module options mix-in."""

  # pylint: disable=no-member

  _MESSAGE_FORMATTERS_DIRECTORY_NAME = 'formatters'
  _MESSAGE_FORMATTERS_FILE_NAME = 'formatters.yaml'

  def __init__(self):
    """Initializes output module options."""
    super(OutputModuleOptions, self).__init__()
    self._output_filename = None
    self._output_format = None
    self._output_module = None

  def _CreateOutputMediator(self):
    """Creates an output mediator.

    Returns:
      OutputMediator: output mediator.

    Raises:
      RuntimeError: if the preferred language identitifier is not supported.
    """
    mediator = output_mediator.OutputMediator(
        self._knowledge_base, data_location=self._data_location,
        preferred_encoding=self.preferred_encoding)

    try:
      mediator.SetPreferredLanguageIdentifier(self._preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    mediator.SetTimezone(self._output_time_zone)

    return mediator

  def _CreateOutputModule(self, mediator, options):
    """Creates an output module.

    Args:
      mediator (OutputMediator): output mediator.
      options (argparse.Namespace): command line arguments.

    Returns:
      OutputModule: output module.

    Raises:
      BadConfigOption: if parameters are missing.
      RuntimeError: if the output module cannot be created.
    """
    try:
      output_module = output_manager.OutputManager.NewOutputModule(
          self._output_format, mediator)

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

  def _ReadMessageFormatters(self, mediator):
    """Reads the message formatters from a formatters file or directory.

    Args:
      mediator (OutputMediator): output mediator.

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
        mediator.ReadMessageFormattersFromDirectory(formatters_directory)
      except KeyError as exception:
        raise errors.BadConfigOption((
            'Unable to read message formatters from directory: {0:s} with '
            'error: {1!s}').format(formatters_directory, exception))

    elif os.path.isfile(formatters_file):
      try:
        mediator.ReadMessageFormattersFromFile(formatters_file)
      except KeyError as exception:
        raise errors.BadConfigOption((
            'Unable to read message formatters from file: {0:s} with error: '
            '{1!s}').format(formatters_file, exception))

    else:
      raise errors.BadConfigOption('Missing formatters file and directory.')

  def ListLanguageIdentifiers(self):
    """Lists the language identifiers."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Identifier', 'Language'],
        title='Language identifiers')
    for language_id, value_list in sorted(
        language_ids.LANGUAGE_IDENTIFIERS.items()):
      table_view.AddRow([language_id, value_list[1]])
    table_view.Write(self._output_writer)

  def _GetOutputModulesInformation(self):
    """Retrieves the output modules information.

    Returns:
      list[tuple[str, str]]: pairs of output module names and descriptions.
    """
    output_modules_information = []
    for name, output_class in output_manager.OutputManager.GetOutputClasses():
      output_modules_information.append((name, output_class.DESCRIPTION))

    return output_modules_information

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

  def _CheckStorageFile(self, storage_file_path, warn_about_existing=False):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path (str): path of the storage file.
      warn_about_existing (bool): True if the user should be warned about
          the storage file already existing.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))

      if warn_about_existing:
        logger.warning('Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          'Unable to write to storage file: {0:s}'.format(storage_file_path))
