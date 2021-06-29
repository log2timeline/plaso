# -*- coding: utf-8 -*-
"""The worker processes CLI arguments helper."""

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
            'If a worker process exceeds this limit it is killed by the main '
            '(foreman) process.'))

    argument_group.add_argument(
        '--worker_timeout', '--worker-timeout', dest='worker_timeout',
        action='store', type=float, metavar='MINUTES', help=(
            'Number of minutes before a worker process that is not providing '
            'status updates is considered inactive. The default timeout is '
            '15.0 minutes. If a worker process exceeds this timeout it is '
            'killed by the main (foreman) process.'))

    argument_group.add_argument(
        '--workers', dest='workers', action='store', type=int, default=0, help=(
            'Number of worker processes. The default is the number of '
            'available system CPUs minus one, for the main (foreman) process.'))

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
          'Invalid number of extraction workers value cannot be less than 0.')

    worker_memory_limit = cls._ParseNumericOption(
        options, 'worker_memory_limit')

    if worker_memory_limit and worker_memory_limit < 0:
      raise errors.BadConfigOption(
          'Invalid worker memory limit value cannot be less than 0.')

    worker_timeout = cls._ParseNumericOption(options, 'worker_timeout')

    if worker_timeout is not None and worker_timeout <= 0.0:
      raise errors.BadConfigOption(
          'Invalid worker timeout value must be larger than 0.0 minutes.')

    setattr(
        configuration_object, '_number_of_extraction_workers',
        number_of_extraction_workers)
    setattr(configuration_object, '_worker_memory_limit', worker_memory_limit)
    setattr(configuration_object, '_worker_timeout', worker_timeout)


manager.ArgumentHelperManager.RegisterHelper(WorkersArgumentsHelper)
