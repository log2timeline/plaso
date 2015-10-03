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
        default=None, metavar=u'HOSTNAME', help=(
            u'The hostname or server IP address of the server.'))
    argument_group.add_argument(
        u'--port', dest=u'port', type=int, action=u'store', default=None,
        metavar=u'PORT', help=u'The port number of the server.')

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not hasattr(output_module, u'SetServerInformation'):
      raise errors.BadConfigObject(u'Unable to set server information.')

    server = cls._ParseStringOption(options, u'server')
    if not server:
      server = cls._DEFAULT_SERVER

    port = getattr(options, u'port', None)
    if port and not isinstance(port, (int, long)):
      raise errors.BadConfigOption(u'Invalid port value not an integer.')

    if not port:
      port = cls._DEFAULT_PORT

    output_module.SetServerInformation(server, port)
