# -*- coding: utf-8 -*-
"""The hashers CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class HashersArgumentsHelper(interface.ArgumentsHelper):
  """Hashers CLI arguments helper."""

  NAME = u'hashers'
  DESCRIPTION = u'Hashers command line arguments.'

  _DEFAULT_HASHER_STRING = u'sha256'

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
        u'--hashers', dest=u'hashers', type=str, action=u'store',
        default=cls._DEFAULT_HASHER_STRING, metavar=u'HASHER_LIST', help=(
            u'Define a list of hashers to use by the tool. This is a comma '
            u'separated list where each entry is the name of a hasher, such as '
            u'"md5,sha256". "all" indicates that all hashers should be '
            u'enabled. "none" disables all hashers. Use "--hashers list" or '
            u'"--info" to list the available hashers.'))

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

    hashers = cls._ParseStringOption(
        options, u'hashers', default_value=cls._DEFAULT_HASHER_STRING)

    # TODO: validate hasher names.

    setattr(configuration_object, u'_hasher_names_string', hashers)


manager.ArgumentHelperManager.RegisterHelper(HashersArgumentsHelper)
