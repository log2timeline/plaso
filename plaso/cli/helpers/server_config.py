# -*- coding: utf-8 -*-
"""The server configuration CLI arguments helper."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.cli.helpers import interface


class ServerArgumentsHelper(interface.ArgumentsHelper):
  """Server configuration CLI arguments helper."""

  NAME = 'server_config'
  DESCRIPTION = 'Argument helper for a server configuration.'

  _DEFAULT_SERVER = '127.0.0.1'
  _DEFAULT_PORT = 80

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '--server', dest='server', type=str, action='store',
        default=cls._DEFAULT_SERVER, metavar='HOSTNAME',
        help='The hostname or server IP address of the server.')
    argument_group.add_argument(
        '--port', dest='port', type=int, action='store',
        default=cls._DEFAULT_PORT, metavar='PORT',
        help='The port number of the server.')

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object does not have the
          SetServerInformation method.
    """
    if not hasattr(output_module, 'SetServerInformation'):
      raise errors.BadConfigObject('Unable to set server information.')

    server = cls._ParseStringOption(
        options, 'server', default_value=cls._DEFAULT_SERVER)
    port = cls._ParseNumericOption(
        options, 'port', default_value=cls._DEFAULT_PORT)

    output_module.SetServerInformation(server, port)
