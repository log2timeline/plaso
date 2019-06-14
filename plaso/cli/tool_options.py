# -*- coding: utf-8 -*-
"""The CLI tool options mix-ins."""

from __future__ import unicode_literals

import os

from plaso.analysis import manager as analysis_manager
from plaso.cli import logger
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.cli.helpers import profiling
from plaso.formatters import mediator as formatters_mediator
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

  def __init__(self):
    """Initializes output module options."""
    super(OutputModuleOptions, self).__init__()
    self._output_filename = None
    self._output_format = None
    self._output_module = None

  def _CreateOutputModule(self, options):
    """Creates the output module.

    Args:
      options (argparse.Namespace): command line arguments.

    Returns:
      OutputModule: output module.

    Raises:
      RuntimeError: if the output module cannot be created.
    """
    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._data_location)

    try:
      formatter_mediator.SetPreferredLanguageIdentifier(
          self._preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    mediator = output_mediator.OutputMediator(
        self._knowledge_base, formatter_mediator,
        preferred_encoding=self.preferred_encoding)
    mediator.SetTimezone(self._preferred_time_zone)

    try:
      output_module = output_manager.OutputManager.NewOutputModule(
          self._output_format, mediator)

    except (KeyError, ValueError) as exception:
      raise RuntimeError(
          'Unable to create output module with error: {0!s}'.format(
              exception))

    if output_manager.OutputManager.IsLinearOutputModule(self._output_format):
      output_file_object = open(self._output_filename, 'wb')
      output_writer = tools.FileObjectOutputWriter(output_file_object)
      output_module.SetOutputWriter(output_writer)

    helpers_manager.ArgumentHelperManager.ParseOptions(options, output_module)

    # Check if there are parameters that have not been defined and need to
    # in order for the output module to continue. Prompt user to supply
    # those that may be missing.
    missing_parameters = output_module.GetMissingArguments()
    while missing_parameters:
      for parameter in missing_parameters:
        value = self._PromptUserForInput(
            'Missing parameter {0:s} for output module'.format(parameter))
        if value is None:
          logger.warning(
              'Unable to set the missing parameter for: {0:s}'.format(
                  parameter))
          continue

        setattr(options, parameter, value)

      helpers_manager.ArgumentHelperManager.ParseOptions(
          options, output_module)
      missing_parameters = output_module.GetMissingArguments()

    return output_module

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

    for name, output_class in output_manager.OutputManager.GetOutputClasses():
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = list(
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
