# -*- coding: utf-8 -*-
"""The temporary directory CLI arguments helper."""

import os

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class TemporaryDirectoryArgumentsHelper(interface.ArgumentsHelper):
  """Temporary directory CLI arguments helper."""

  NAME = 'temporary_directory'
  DESCRIPTION = 'Temporary directory command line arguments.'

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
        '--temporary_directory', '--temporary-directory',
        dest='temporary_directory', type=str, action='store',
        metavar='DIRECTORY', help=(
            'Path to the directory that should be used to store temporary '
            'files created during processing.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when the temporary directory does not exists.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    temporary_directory = getattr(options, 'temporary_directory', None)
    if temporary_directory and not os.path.isdir(temporary_directory):
      raise errors.BadConfigOption(
          'No such temporary directory: {0:s}'.format(temporary_directory))

    setattr(configuration_object, '_temporary_directory', temporary_directory)


manager.ArgumentHelperManager.RegisterHelper(TemporaryDirectoryArgumentsHelper)
