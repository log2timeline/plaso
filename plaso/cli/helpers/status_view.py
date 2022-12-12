# -*- coding: utf-8 -*-
"""The status view CLI arguments helper."""

from plaso.cli import status_view
from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class StatusViewArgumentsHelper(interface.ArgumentsHelper):
  """Status view CLI arguments helper."""

  NAME = 'status_view'
  DESCRIPTION = 'Status view command line arguments.'

  _STATUS_VIEW_TYPES = ['file', 'linear', 'none', 'window']

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
        '--status_view', '--status-view', dest='status_view_mode',
        choices=cls._STATUS_VIEW_TYPES, action='store', metavar='TYPE',
        default=status_view.StatusView.MODE_WINDOW, help=(
            'The processing status view mode: "file", "linear", "none" or '
            '"window".'))

    argument_group.add_argument(
        '--status_view_file', '--status-view-file', dest='status_view_file',
        action='store', metavar='PATH', default='status.info', help=(
            'The name of the status view file.'))

    argument_group.add_argument(
        '--status_view_interval', '--status-view-interval',
        dest='status_view_interval', action='store', type=float,
        metavar='SECONDS', default=0.5, help=(
            'Number of seconds to update the status view.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    status_view_mode = cls._ParseStringOption(
        options, 'status_view_mode',
        default_value=status_view.StatusView.MODE_WINDOW)

    status_view_file = cls._ParseStringOption(
        options, 'status_view_file', default_value='status.info')

    status_view_interval = cls._ParseNumericOption(
        options, 'status_view_interval')

    if status_view_interval is None or status_view_interval <= 0.0:
      raise errors.BadConfigOption(
          'Invalid status view interval value must be larger than 0.0 seconds.')

    setattr(configuration_object, '_status_view_mode', status_view_mode)
    setattr(configuration_object, '_status_view_file', status_view_file)
    setattr(configuration_object, '_status_view_interval', status_view_interval)


manager.ArgumentHelperManager.RegisterHelper(StatusViewArgumentsHelper)
