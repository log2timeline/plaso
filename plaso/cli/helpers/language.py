# -*- coding: utf-8 -*-
"""The language CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.helpers import language_tags
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
        '--language', metavar='LANGUAGE_TAG', dest='preferred_language',
        default=None, type=str, help=(
            'The preferred language, which is used for extracting and '
            'formatting Windows EventLog message strings. Use "--language '
            'list" to see a list of supported language tags. The en-US (LCID '
            '0x0409) language is used as fallback if preprocessing could not '
            'determine the system language or no language information is '
            'available in the winevt-rc.db database.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when the language tag is not supported.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    language_tag = cls._ParseStringOption(options, 'preferred_language')

    if (language_tag and language_tag != 'list' and
        not language_tags.LanguageTagHelper.IsLanguageTag(language_tag)):
      raise errors.BadConfigOption(
          'Unsupported preferred language tag: {0!s}'.format(language_tag))

    setattr(configuration_object, '_preferred_language', language_tag)


manager.ArgumentHelperManager.RegisterHelper(LanguageArgumentsHelper)
