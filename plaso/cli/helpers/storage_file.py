# -*- coding: utf-8 -*-
"""The storage file CLI arguments helper."""

from __future__ import unicode_literals

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class StorageFileArgumentsHelper(interface.ArgumentsHelper):
  """Storage file CLI arguments helper."""

  NAME = 'storage_file'
  DESCRIPTION = 'Storage file command line arguments.'

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
        'storage_file', metavar='STORAGE_FILE', nargs='?', type=str,
        default=None, help='Path to a storage file.')

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

    storage_file = cls._ParseStringOption(options, 'storage_file')

    setattr(configuration_object, '_storage_file_path', storage_file)


manager.ArgumentHelperManager.RegisterHelper(StorageFileArgumentsHelper)
