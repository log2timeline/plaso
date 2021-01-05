# -*- coding: utf-8 -*-
"""The parsers CLI arguments helper."""

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
    argument_group.add_argument(
        '--parsers', dest='parsers', type=str, action='store',
        default='', metavar='PARSER_FILTER_EXPRESSION', help=(
            'Define which presets, parsers and/or plugins to use, or show '
            'possible values. The expression is a comma separated string '
            'where each element is a preset, parser or plugin name. Each '
            'element can be prepended with an exclamation mark to exclude the '
            'item. Matching is case insensitive. Examples: "linux,'
            '!bash_history" enables the linux preset, without the '
            'bash_history parser. "sqlite,!sqlite/chrome_history" enables '
            'all sqlite plugins except for chrome_history". "win7,syslog" '
            'enables the win7 preset, as well as the syslog parser. Use '
            '"--parsers list" or "--info" to list available presets, parsers '
            'and plugins.'))

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
