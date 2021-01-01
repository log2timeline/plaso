# -*- coding: utf-8 -*-
"""The storage format CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import definitions
from plaso.lib import errors


class StorageFormatArgumentsHelper(interface.ArgumentsHelper):
  """Storage format CLI arguments helper."""

  NAME = 'storage_format'
  DESCRIPTION = 'Storage format command line arguments.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    session_storage_formats = sorted(definitions.SESSION_STORAGE_FORMATS)
    task_storage_formats = sorted(definitions.TASK_STORAGE_FORMATS)

    argument_group.add_argument(
        '--storage_format', '--storage-format', action='store',
        choices=session_storage_formats, dest='storage_format', type=str,
        metavar='FORMAT', default=definitions.DEFAULT_STORAGE_FORMAT, help=(
            'Format of the storage file, the default is: {0:s}. Supported '
            'options: {1:s}'.format(
                definitions.DEFAULT_STORAGE_FORMAT,
                ', '.join(session_storage_formats))))

    argument_group.add_argument(
        '--task_storage_format', '--task-storage-format', action='store',
        choices=task_storage_formats, dest='task_storage_format', type=str,
        metavar='FORMAT', default=definitions.DEFAULT_STORAGE_FORMAT, help=(
            'Format for task storage, the default is: {0:s}. Supported '
            'options: {1:s}'.format(
                definitions.DEFAULT_STORAGE_FORMAT,
                ', '.join(task_storage_formats))))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: if the storage format or task storage is not defined
          or supported.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    storage_format = cls._ParseStringOption(options, 'storage_format')
    if not storage_format:
      raise errors.BadConfigOption('Unable to determine storage format.')

    if storage_format not in definitions.SESSION_STORAGE_FORMATS:
      raise errors.BadConfigOption(
          'Unsupported storage format: {0:s}'.format(storage_format))

    setattr(configuration_object, '_storage_format', storage_format)

    task_storage_format = cls._ParseStringOption(options, 'task_storage_format')
    if not task_storage_format:
      raise errors.BadConfigOption('Unable to determine task storage format.')

    if task_storage_format not in definitions.TASK_STORAGE_FORMATS:
      raise errors.BadConfigOption(
          'Unsupported task storage format: {0:s}'.format(task_storage_format))

    setattr(configuration_object, '_task_storage_format', task_storage_format)


manager.ArgumentHelperManager.RegisterHelper(StorageFormatArgumentsHelper)
