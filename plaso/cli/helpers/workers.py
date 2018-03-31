# -*- coding: utf-8 -*-
"""The worker processes CLI arguments helper."""

from __future__ import unicode_literals

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class WorkersArgumentsHelper(interface.ArgumentsHelper):
  """Worker processes CLI arguments helper."""

  NAME = 'workers'
  DESCRIPTION = 'Worker processes command line arguments.'

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
        '--worker_memory_limit', '--worker-memory-limit',
        dest='worker_memory_limit', action='store', type=int,
        metavar='SIZE', help=(
            'Maximum amount of memory (data segment and shared memory) '
            'a worker process is allowed to consume in bytes, where 0 '
            'represents no limit. The default limit is 2147483648 (2 GiB). '
            'If a worker process exceeds this limit is is killed by the main '
            '(foreman) process.'))

    argument_group.add_argument(
        '--workers', dest='workers', action='store', type=int, default=0, help=(
            'Number of worker processes [defaults to available system CPUs '
            'minus one].'))

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

    number_of_extraction_workers = cls._ParseNumericOption(
        options, 'workers', default_value=0)

    if number_of_extraction_workers < 0:
      raise errors.BadConfigOption(
          'Invalid number of extraction workers value cannot be negative.')

    worker_memory_limit = cls._ParseNumericOption(
        options, 'worker_memory_limit')

    if worker_memory_limit and worker_memory_limit < 0:
      raise errors.BadConfigOption(
          'Invalid worker memory limit value cannot be negative.')

    setattr(
        configuration_object, '_number_of_extraction_workers',
        number_of_extraction_workers)
    setattr(configuration_object, '_worker_memory_limit', worker_memory_limit)


manager.ArgumentHelperManager.RegisterHelper(WorkersArgumentsHelper)
