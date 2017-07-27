# -*- coding: utf-8 -*-
"""The server configuration CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface


class ServerArgumentsHelper(interface.ArgumentsHelper):
  """Server configuration CLI arguments helper."""

  NAME = u'server_config'
  DESCRIPTION = u'Argument helper for a server configuration.'

  _DEFAULT_SERVER = u'127.0.0.1'
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
        u'--server', dest=u'server', type=str, action=u'store',
        default=cls._DEFAULT_SERVER, metavar=u'HOSTNAME',
        help=u'The hostname or server IP address of the server.')
    argument_group.add_argument(
        u'--port', dest=u'port', type=int, action=u'store',
        default=cls._DEFAULT_PORT, metavar=u'PORT',
        help=u'The port number of the server.')

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
    if not hasattr(output_module, u'SetServerInformation'):
      raise errors.BadConfigObject(u'Unable to set server information.')

    server = cls._ParseStringOption(
        options, u'server', default_value=cls._DEFAULT_SERVER)
    port = cls._ParseNumericOption(
        options, u'port', default_value=cls._DEFAULT_PORT)

    output_module.SetServerInformation(server, port)
