# -*- coding: utf-8 -*-
"""The CLI tool options mix-ins."""

import logging
import os

from plaso.analysis import manager as analysis_manager
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import errors
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator


# TODO: pass argument_parser instead of argument_group and add groups
# in mix-ins.


class AnalysisPluginOptions(object):
  """Analysis plugin options mix-in."""

  def _CreateAnalysisPlugins(self, options):
    """Creates the analysis plugins.

    Args:
      options (argparse.Namespace): command line arguments.

    Returns:
      list[AnalysisPlugin]: analysis plugins.
    """
    if not self._analysis_plugins:
      return

    analysis_plugins = (
        analysis_manager.AnalysisPluginManager.GetPluginObjects(
            self._analysis_plugins))

    for analysis_plugin in analysis_plugins:
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
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Analysis Plugins')
    # TODO: add support for a 3 column table.
    for name, description, type_string in analysis_plugin_info:
      description = u'{0:s} [{1:s}]'.format(description, type_string)
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)


class OutputModuleOptions(object):
  """Output module options mix-in."""

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
          u'Unable to create output module with error: {0:s}'.format(
              exception))

    if output_manager.OutputManager.IsLinearOutputModule(self._output_format):
      output_file_object = open(self._output_filename, u'wb')
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
            u'Missing parameter {0:s} for output module'.format(parameter))
        if value is None:
          logging.warning(
              u'Unable to set the missing parameter for: {0:s}'.format(
                  parameter))
          continue

        setattr(options, parameter, value)

      helpers_manager.ArgumentHelperManager.ParseOptions(
          options, output_module)
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

  def ListOutputModules(self):
    """Lists the output modules."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=[u'Name', u'Description'],
        title=u'Output Modules')

    for name, output_class in output_manager.OutputManager.GetOutputClasses():
      table_view.AddRow([name, output_class.DESCRIPTION])
    table_view.Write(self._output_writer)

    disabled_classes = list(
        output_manager.OutputManager.GetDisabledOutputClasses())
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
