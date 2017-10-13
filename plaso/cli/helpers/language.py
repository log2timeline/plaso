# -*- coding: utf-8 -*-
"""The language CLI arguments helper."""

from __future__ import unicode_literals

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class LanguageArgumentsHelper(interface.ArgumentsHelper):
  """Language CLI arguments helper."""

  NAME = 'language'
  DESCRIPTION = 'Language command line arguments.'

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
        '--language', metavar='LANGUAGE', dest='preferred_language',
        default='en-US', type=str, help=(
            'The preferred language identifier for Windows Event Log message '
            'strings. Use "--language list" to see a list of available '
            'language identifiers. Note that formatting will fall back on '
            'en-US (LCID 0x0409) if the preferred language is not available '
            'in the database of message string templates.'))

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

    preferred_language = cls._ParseStringOption(
        options, 'preferred_language', default_value='en-US')

    setattr(configuration_object, '_preferred_language', preferred_language)


manager.ArgumentHelperManager.RegisterHelper(LanguageArgumentsHelper)
