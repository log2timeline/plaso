# -*- coding: utf-8 -*-
"""The analysis plugins CLI arguments helper."""

import sys

from plaso.analysis import manager as analysis_manager
from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class AnalysisPluginsArgumentsHelper(interface.ArgumentsHelper):
  """Analysis plugins CLI arguments helper."""

  NAME = u'analysis_plugins'
  DESCRIPTION = u'Analysis plugins command line arguments.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        u'--analysis', metavar=u'PLUGIN_LIST', dest=u'analysis_plugins',
        default=u'', action=u'store', type=str, help=(
            u'A comma separated list of analysis plugin names to be loaded '
            u'or "--analysis list" to see a list of available plugins.'))

    arguments = sys.argv[1:]
    argument_index = 0

    if u'--analysis' in arguments:
      argument_index = arguments.index(u'--analysis') + 1

    if argument_index > 0 and argument_index < len(arguments):
      names = [name.strip() for name in arguments[argument_index].split(u',')]
    else:
      names = None

    if names and names != [u'list']:
      manager.ArgumentHelperManager.AddCommandLineArguments(
          argument_group, category=u'analysis', names=names)

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          u'Configuration object is not an instance of CLITool')

    plugin_names_argument = cls._ParseStringOption(options, u'analysis_plugins')

    if plugin_names_argument and plugin_names_argument != u'list':
      available_plugin_names = (
          analysis_manager.AnalysisPluginManager.GetPluginNames())
      plugin_names_argument = [
          name.strip() for name in plugin_names_argument.split(u',')]

      difference = set(plugin_names_argument).difference(available_plugin_names)
      if difference:
        raise errors.BadConfigOption(
            u'Non-existent analysis plugins specified: {0:s}'.format(
                u' '.join(difference)))

    setattr(configuration_object, u'_analysis_plugins', plugin_names_argument)


manager.ArgumentHelperManager.RegisterHelper(AnalysisPluginsArgumentsHelper)
