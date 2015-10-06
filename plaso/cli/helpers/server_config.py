# -*- coding: utf-8 -*-
"""The arguments helper for a server configuration."""

from plaso.lib import errors
from plaso.cli.helpers import interface


class BaseServerConfigHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for server configuration."""

  NAME = u'server_config'
  DESCRIPTION = u'Argument helper for a server configuration.'

  _DEFAULT_SERVER = u'127.0.0.1'
  _DEFAULT_PORT = 80

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
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
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not hasattr(output_module, u'SetServerInformation'):
      raise errors.BadConfigObject(u'Unable to set server information.')

    server = cls._ParseStringOption(
        options, u'server', default_value=cls._DEFAULT_SERVER)
    port = cls._ParseIntegerOption(
        options, u'port', default_value=cls._DEFAULT_PORT)

    output_module.SetServerInformation(server, port)
