# -*- coding: utf-8 -*-
"""The sessionize analysis plugin CLI arguments helper."""

from plaso.analysis import sessionize
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class SessionizeAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Sessionize analysis plugin CLI arguments helper."""

  NAME = 'sessionize'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the Sessionize analysis plugin.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '--maximum-pause', '--maximum_pause', dest='sessionize_maximumpause',
        type=int, action='store', metavar='MINUTES', default=10, help=(
            'Specify the maximum delay in minutes between events in the '
            'session.'))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      analysis_plugin (OutputModule): analysis_plugin to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(analysis_plugin, sessionize.SessionizeAnalysisPlugin):
      raise errors.BadConfigObject(
          'Analysis plugin is not an instance of SessionizeAnalysisPlugin')

    maximum_pause = cls._ParseNumericOption(
        options, 'sessionize_maximumpause', default_value=10)

    if maximum_pause <= 0:
      raise errors.BadConfigOption(
          'Maximum pause value {0:d} is not supported. '
          'Value must be greater than 0.'.format(maximum_pause))
    analysis_plugin.SetMaximumPause(maximum_pause)


manager.ArgumentHelperManager.RegisterHelper(SessionizeAnalysisArgumentsHelper)
