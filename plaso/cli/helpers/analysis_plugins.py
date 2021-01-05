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

  NAME = 'analysis_plugins'
  DESCRIPTION = 'Analysis plugins command line arguments.'

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
        '--analysis', metavar='PLUGIN_LIST', dest='analysis_plugins',
        default='', action='store', type=str, help=(
            'A comma separated list of analysis plugin names to be loaded '
            'or "--analysis list" to see a list of available plugins.'))

    arguments = sys.argv[1:]
    argument_index = 0

    if '--analysis' in arguments:
      argument_index = arguments.index('--analysis') + 1

    if 0 < argument_index < len(arguments):
      names = [name.strip() for name in arguments[argument_index].split(',')]
    else:
      names = None

    if names and names != ['list']:
      manager.ArgumentHelperManager.AddCommandLineArguments(
          argument_group, category='analysis', names=names)

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when non-existing analysis plugins are specified.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    analysis_plugins = cls._ParseStringOption(options, 'analysis_plugins')

    if analysis_plugins and analysis_plugins.lower() != 'list':
      plugin_names = analysis_manager.AnalysisPluginManager.GetPluginNames()
      analysis_plugins = [name.strip() for name in analysis_plugins.split(',')]

      difference = set(analysis_plugins).difference(plugin_names)
      if difference:
        raise errors.BadConfigOption(
            'Non-existent analysis plugins specified: {0:s}'.format(
                ' '.join(difference)))

    setattr(configuration_object, '_analysis_plugins', analysis_plugins)


manager.ArgumentHelperManager.RegisterHelper(AnalysisPluginsArgumentsHelper)
