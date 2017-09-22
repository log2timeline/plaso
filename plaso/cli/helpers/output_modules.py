# -*- coding: utf-8 -*-
"""The output modules CLI arguments helper."""

import os
import sys

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors
from plaso.output import manager as output_manager


class OutputModulesArgumentsHelper(interface.ArgumentsHelper):
  """Output modules CLI arguments helper."""

  NAME = u'output_modules'
  DESCRIPTION = u'Output modules command line arguments.'

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
        u'-o', u'--output_format', u'--output-format', metavar=u'FORMAT',
        dest=u'output_format', default=u'dynamic', help=(
            u'The output format. Use "-o list" to see a list of available '
            u'output formats.'))

    argument_group.add_argument(
        u'-w', u'--write', metavar=u'OUTPUT_FILE', dest=u'write',
        help=u'Output filename.')

    # TODO: determine if this is repeated elsewhere and refactor this into
    # a helper function.
    arguments = sys.argv[1:]
    argument_index = 0

    if u'-o' in arguments:
      argument_index = arguments.index(u'-o') + 1
    elif u'--output_format' in arguments:
      argument_index = arguments.index(u'--output_format') + 1
    elif u'--output-format' in arguments:
      argument_index = arguments.index(u'--output-format') + 1

    if argument_index > 0 and argument_index < len(arguments):
      names = [name.strip() for name in arguments[argument_index].split(u',')]
    else:
      names = [u'dynamic']

    if names and names != [u'list']:
      manager.ArgumentHelperManager.AddCommandLineArguments(
          argument_group, category=u'output', names=names)

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
          u'Configuration object is not an instance of CLITool')

    output_format = getattr(options, u'output_format', u'dynamic')
    output_filename = getattr(options, u'write', None)

    if output_format != u'list':
      if not output_manager.OutputManager.HasOutputClass(output_format):
        raise errors.BadConfigOption(
            u'Unsupported output format: {0:s}.'.format(output_format))

    if output_manager.OutputManager.IsLinearOutputModule(output_format):
      if not output_filename:
        raise errors.BadConfigOption((
            u'Output format: {0:s} requires an output file').format(
                output_format))

      if os.path.exists(output_filename):
        raise errors.BadConfigOption(
            u'Output file already exists: {0:s}.'.format(output_filename))

    setattr(configuration_object, u'_output_format', output_format)
    setattr(configuration_object, u'_output_filename', output_filename)


manager.ArgumentHelperManager.RegisterHelper(OutputModulesArgumentsHelper)
