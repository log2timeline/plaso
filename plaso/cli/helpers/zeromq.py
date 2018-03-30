# -*- coding: utf-8 -*-
"""The ZeroMQ CLI arguments helper."""

from __future__ import unicode_literals

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ZeroMQArgumentsHelper(interface.ArgumentsHelper):
  """ZeroMQ CLI arguments helper."""

  NAME = 'zeromq'
  DESCRIPTION = 'ZeroMQ command line arguments.'

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
        '--disable_zeromq', '--disable-zeromq', action='store_false',
        dest='use_zeromq', default=True, help=(
            'Disable queueing using ZeroMQ. A Multiprocessing queue will be '
            'used instead.'))

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

    use_zeromq = getattr(options, 'use_zeromq', True)

    setattr(configuration_object, '_use_zeromq', use_zeromq)


manager.ArgumentHelperManager.RegisterHelper(ZeroMQArgumentsHelper)
