# -*- coding: utf-8 -*-
"""The YARA rules CLI arguments helper."""

import io

import yara

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class YaraRulesArgumentsHelper(interface.ArgumentsHelper):
  """YARA rules CLI arguments helper."""

  NAME = 'yara_rules'
  DESCRIPTION = 'YARA rules command line arguments.'

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
        '--yara_rules', '--yara-rules', dest='yara_rules_path',
        type=str, metavar='PATH', action='store', help=(
            'Path to a file containing Yara rules definitions.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when the Yara rules file cannot be read or parsed.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    yara_rules_string = None

    path = getattr(options, 'yara_rules_path', None)
    if path:
      try:
        with io.open(path, 'rt', encoding='utf-8') as rules_file:
          yara_rules_string = rules_file.read()

      except IOError as exception:
        raise errors.BadConfigOption(
            'Unable to read Yara rules file: {0:s} with error: {1!s}'.format(
                path, exception))

      try:
        # We try to parse the rules here, to check that the definitions are
        # valid. We then pass the string definitions along to the workers, so
        # that they don't need read access to the rules file.
        yara.compile(source=yara_rules_string)

      except yara.Error as exception:
        raise errors.BadConfigOption(
            'Unable to parse Yara rules in: {0:s} with error: {1!s}'.format(
                path, exception))

    setattr(configuration_object, '_yara_rules_string', yara_rules_string)


manager.ArgumentHelperManager.RegisterHelper(YaraRulesArgumentsHelper)
