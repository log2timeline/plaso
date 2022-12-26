# -*- coding: utf-8 -*-
"""The profiling CLI arguments helper."""

import os

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ProfilingArgumentsHelper(interface.ArgumentsHelper):
  """Profiling CLI arguments helper."""

  NAME = 'profiling'
  DESCRIPTION = 'Profiling command line arguments.'

  DEFAULT_PROFILING_SAMPLE_RATE = 1000

  PROFILERS_INFORMATION = {
      'analyzers': 'Profile CPU time of analyzers, like hashing',
      'format_checks': 'Profile CPU time per format check',
      'memory': 'Profile memory usage over time',
      'parsers': 'Profile CPU time per parser',
      'processing': 'Profile CPU time of processing phases',
      'serializers': 'Profile CPU time of serialization',
      'storage': 'Profile storage reads and writes',
      'task_queue': 'Profile task queue status (multi-processing only)',
      'tasks': 'Profile the status of tasks (multi-processing only)'}

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
        '--profilers', dest='profilers', type=str, action='store',
        default='', metavar='PROFILERS_LIST', help=(
            'List of profilers to use by the tool. This is a comma separated '
            'list where each entry is the name of a profiler. Use '
            '"--profilers list" to list the available profilers.'))

    argument_group.add_argument(
        '--profiling_directory', '--profiling-directory',
        dest='profiling_directory', type=str, action='store',
        metavar='DIRECTORY', help=(
            'Path to the directory that should be used to store the profiling '
            'sample files. By default the sample files are stored in the '
            'current working directory.'))

    argument_group.add_argument(
        '--profiling_sample_rate', '--profiling-sample-rate',
        dest='profiling_sample_rate', action='store', metavar='SAMPLE_RATE',
        default=0, help=(
            'Profiling sample rate (defaults to a sample every {0:d} '
            'files).').format(cls.DEFAULT_PROFILING_SAMPLE_RATE))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when the configuration options are missing or not
          supported.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    profilers = cls._ParseStringOption(options, 'profilers')

    if not profilers:
      profilers = set()
    elif profilers.lower() != 'list':
      profilers = set(profilers.split(','))

      supported_profilers = set(cls.PROFILERS_INFORMATION.keys())
      unsupported_profilers = profilers.difference(supported_profilers)
      if unsupported_profilers:
        unsupported_profilers = ', '.join(unsupported_profilers)
        raise errors.BadConfigOption(
            'Unsupported profilers: {0:s}'.format(unsupported_profilers))

    profiling_directory = getattr(options, 'profiling_directory', None)
    if profiling_directory and not os.path.isdir(profiling_directory):
      raise errors.BadConfigOption(
          'No such profiling directory: {0:s}'.format(profiling_directory))

    profiling_sample_rate = getattr(options, 'profiling_sample_rate', None)
    if not profiling_sample_rate:
      profiling_sample_rate = cls.DEFAULT_PROFILING_SAMPLE_RATE
    else:
      try:
        profiling_sample_rate = int(profiling_sample_rate, 10)
      except (TypeError, ValueError):
        raise errors.BadConfigOption(
            'Invalid profile sample rate: {0!s}.'.format(profiling_sample_rate))

    setattr(configuration_object, '_profilers', profilers)
    setattr(configuration_object, '_profiling_directory', profiling_directory)
    setattr(
        configuration_object, '_profiling_sample_rate', profiling_sample_rate)


manager.ArgumentHelperManager.RegisterHelper(ProfilingArgumentsHelper)
