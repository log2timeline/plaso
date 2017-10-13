# -*- coding: utf-8 -*-
"""The parsers CLI arguments helper."""

from __future__ import unicode_literals

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ParsersArgumentsHelper(interface.ArgumentsHelper):
  """Parsers CLI arguments helper."""

  NAME = 'parsers'
  DESCRIPTION = 'Parsers command line arguments.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    # TODO: rename option name to parser_filter_expression.
    argument_group.add_argument(
        '--parsers', dest='parsers', type=str, action='store',
        default='', metavar='PARSER_LIST', help=(
            'Define a list of parsers to use by the tool. This is a comma '
            'separated list where each entry can be either a name of a parser '
            'or a parser list. Each entry can be prepended with an '
            'exclamation mark to negate the selection (exclude it). The list '
            'match is an exact match while an individual parser matching is '
            'a case insensitive substring match, with support for glob '
            'patterns. Examples would be: "reg" that matches the substring '
            '"reg" in all parser names or the glob pattern "sky[pd]" that '
            'would match all parsers that have the string "skyp" or "skyd" '
            'in its name. All matching is case insensitive. Use "--parsers '
            'list" or "--info" to list the available parsers.'))

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

    parsers = cls._ParseStringOption(options, 'parsers', default_value='')
    parsers = parsers.replace('\\', '/')

    # TODO: validate parser names.

    setattr(configuration_object, '_parser_filter_expression', parsers)


manager.ArgumentHelperManager.RegisterHelper(ParsersArgumentsHelper)
