# -*- coding: utf-8 -*-
"""The text prepend CLI arguments helper."""

from __future__ import unicode_literals

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class TextPrependArgumentsHelper(interface.ArgumentsHelper):
  """Text prepend CLI arguments helper."""

  NAME = 'text_prepend'
  DESCRIPTION = 'Text prepend command line arguments.'

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
        '-t', '--text', dest='text_prepend', action='store', type=str,
        default='', metavar='TEXT', help=(
            'Define a free form text string that is prepended to each path '
            'to make it easier to distinguish one record from another in a '
            'timeline (like c:\\, or host_w_c:\\)'))

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

    text_prepend = cls._ParseStringOption(options, 'text_prepend')

    setattr(configuration_object, '_text_prepend', text_prepend)


manager.ArgumentHelperManager.RegisterHelper(TextPrependArgumentsHelper)
