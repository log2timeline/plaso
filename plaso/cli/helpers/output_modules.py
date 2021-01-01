# -*- coding: utf-8 -*-
"""The output modules CLI arguments helper."""

import sys

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors
from plaso.output import manager as output_manager


class OutputModulesArgumentsHelper(interface.ArgumentsHelper):
  """Output modules CLI arguments helper."""

  NAME = 'output_modules'
  DESCRIPTION = 'Output modules command line arguments.'

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
        '-o', '--output_format', '--output-format', metavar='FORMAT',
        dest='output_format', default='dynamic', help=(
            'The output format. Use "-o list" to see a list of available '
            'output formats.'))

    argument_group.add_argument(
        '-w', '--write', metavar='OUTPUT_FILE', dest='write',
        help='Output filename.')

    # TODO: determine if this is repeated elsewhere and refactor this into
    # a helper function.
    arguments = sys.argv[1:]
    argument_index = 0

    if '-o' in arguments:
      argument_index = arguments.index('-o') + 1
    elif '--output_format' in arguments:
      argument_index = arguments.index('--output_format') + 1
    elif '--output-format' in arguments:
      argument_index = arguments.index('--output-format') + 1

    if 0 < argument_index < len(arguments):
      names = [name.strip() for name in arguments[argument_index].split(',')]
    else:
      names = ['dynamic']

    if names and names != ['list']:
      manager.ArgumentHelperManager.AddCommandLineArguments(
          argument_group, category='output', names=names)

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when the output format is not supported or the output
          is not provided or already exists.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    output_format = getattr(options, 'output_format', 'dynamic')
    output_filename = getattr(options, 'write', None)

    if output_format != 'list':
      if not output_manager.OutputManager.HasOutputClass(output_format):
        raise errors.BadConfigOption(
            'Unsupported output format: {0:s}.'.format(output_format))

    setattr(configuration_object, '_output_format', output_format)
    setattr(configuration_object, '_output_filename', output_filename)


manager.ArgumentHelperManager.RegisterHelper(OutputModulesArgumentsHelper)
