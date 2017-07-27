# -*- coding: utf-8 -*-
"""The parsers CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ParsersArgumentsHelper(interface.ArgumentsHelper):
  """Parsers CLI arguments helper."""

  NAME = u'parsers'
  DESCRIPTION = u'Parsers command line arguments.'

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
        u'--parsers', dest=u'parsers', type=str, action=u'store',
        default=u'', metavar=u'PARSER_LIST', help=(
            u'Define a list of parsers to use by the tool. This is a comma '
            u'separated list where each entry can be either a name of a parser '
            u'or a parser list. Each entry can be prepended with an '
            u'exclamation mark to negate the selection (exclude it). The list '
            u'match is an exact match while an individual parser matching is '
            u'a case insensitive substring match, with support for glob '
            u'patterns. Examples would be: "reg" that matches the substring '
            u'"reg" in all parser names or the glob pattern "sky[pd]" that '
            u'would match all parsers that have the string "skyp" or "skyd" '
            u'in its name. All matching is case insensitive. Use "--parsers '
            u'list" or "--info" to list the available parsers.'))

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

    parsers = cls._ParseStringOption(options, u'parsers', default_value=u'')
    parsers = parsers.replace(u'\\', u'/')

    # TODO: validate parser names.

    setattr(configuration_object, u'_parser_filter_expression', parsers)


manager.ArgumentHelperManager.RegisterHelper(ParsersArgumentsHelper)
