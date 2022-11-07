# -*- coding: utf-8 -*-
"""The VFS back-end CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class VFSBackEndArgumentsHelper(interface.ArgumentsHelper):
  """VFS back-end CLI arguments helper."""

  NAME = 'vfs_backend'
  DESCRIPTION = 'dfVFS back-end command line arguments.'

  _SUPPORTED_VFS_BACK_ENDS = [
      'auto', 'fsext', 'fsfat', 'fshfs', 'fsntfs', 'tsk', 'vsgpt']

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
        '--vfs_back_end', '--vfs-back-end', dest='vfs_back_end',
        choices=cls._SUPPORTED_VFS_BACK_ENDS, action='store', metavar='TYPE',
        default='auto', help=(
            'The preferred dfVFS back-end: "auto", "fsext", "fsfat", "fshfs", '
            '"fsntfs", "tsk" or "vsgpt".'))

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
          'Configuration object is not an instance of CLITool')

    vfs_back_end = cls._ParseStringOption(options, 'vfs_back_end')

    setattr(configuration_object, '_vfs_back_end', vfs_back_end)


manager.ArgumentHelperManager.RegisterHelper(VFSBackEndArgumentsHelper)
