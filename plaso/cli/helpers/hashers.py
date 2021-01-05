# -*- coding: utf-8 -*-
"""The hashers CLI arguments helper."""

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class HashersArgumentsHelper(interface.ArgumentsHelper):
  """Hashers CLI arguments helper."""

  NAME = 'hashers'
  DESCRIPTION = 'Hashers command line arguments.'

  _DEFAULT_HASHER_STRING = 'sha256'

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
        '--hasher_file_size_limit', '--hasher-file-size-limit',
        dest='hasher_file_size_limit', type=int, action='store', default=0,
        metavar='SIZE', help=(
            'Define the maximum file size in bytes that hashers should '
            'process. Any larger file will be skipped. A size of 0 represents '
            'no limit.'))

    argument_group.add_argument(
        '--hashers', dest='hashers', type=str, action='store',
        default=cls._DEFAULT_HASHER_STRING, metavar='HASHER_LIST', help=(
            'Define a list of hashers to use by the tool. This is a comma '
            'separated list where each entry is the name of a hasher, such as '
            '"md5,sha256". "all" indicates that all hashers should be '
            'enabled. "none" disables all hashers. Use "--hashers list" or '
            '"--info" to list the available hashers.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    hashers = cls._ParseStringOption(
        options, 'hashers', default_value=cls._DEFAULT_HASHER_STRING)

    hasher_file_size_limit = cls._ParseNumericOption(
        options, 'hasher_file_size_limit', default_value=0)

    # TODO: validate hasher names.

    if hasher_file_size_limit < 0:
      raise errors.BadConfigOption(
          'Invalid hasher file size limit value cannot be negative.')

    setattr(configuration_object, '_hasher_names_string', hashers)
    setattr(
        configuration_object, '_hasher_file_size_limit', hasher_file_size_limit)


manager.ArgumentHelperManager.RegisterHelper(HashersArgumentsHelper)
