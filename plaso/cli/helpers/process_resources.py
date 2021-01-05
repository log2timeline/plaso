# -*- coding: utf-8 -*-
"""The process resources CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ProcessResourcesArgumentsHelper(interface.ArgumentsHelper):
  """Process resources CLI arguments helper."""

  NAME = 'process_resources'
  DESCRIPTION = 'Process resources command line arguments.'

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
        '--process_memory_limit', '--process-memory-limit',
        dest='process_memory_limit', action='store', type=int,
        metavar='SIZE', help=(
            'Maximum amount of memory (data segment) a process is allowed '
            'to allocate in bytes, where 0 represents no limit. The default '
            'limit is 4294967296 (4 GiB). This applies to both the main '
            '(foreman) process and the worker processes. This limit is '
            'enforced by the operating system and will supersede the worker '
            'memory limit (--worker_memory_limit).'))

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

    process_memory_limit = cls._ParseNumericOption(
        options, 'process_memory_limit')

    if process_memory_limit and process_memory_limit < 0:
      raise errors.BadConfigOption(
          'Invalid process memory limit value cannot be negative.')

    setattr(configuration_object, '_process_memory_limit', process_memory_limit)


manager.ArgumentHelperManager.RegisterHelper(ProcessResourcesArgumentsHelper)
