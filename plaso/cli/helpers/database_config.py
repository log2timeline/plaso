# -*- coding: utf-8 -*-
"""The arguments helper for a database configuration."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import server_config


class DatabaseConfigHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for database configuration."""

  NAME = u'database_config'
  DESCRIPTION = u'Argument helper for a database configuration.'

  _DEFAULT_NAME = u'data'
  _DEFAULT_PASSWORD = u'toor'
  _DEFAULT_USERNAME = u'root'

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
        u'--user', dest=u'username', type=str, action=u'store',
        default=None, metavar=u'USERNAME', required=False, help=(
            u'The username used to connect to the database.'))
    argument_group.add_argument(
        u'--password', dest=u'password', type=str, action=u'store',
        default=None, metavar=u'PASSWORD', help=(
            u'The password for the database user.'))
    argument_group.add_argument(
        u'--db_name', '--db-name', dest=u'db_name', action=u'store',
        type=str, default=None, required=False, help=(
            u'The name of the database to connect to.'))

    server_config.BaseServerConfigHelper.AddArguments(argument_group)

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
    if not hasattr(output_module, u'SetCredentials'):
      raise errors.BadConfigObject(u'Unable to set username information.')

    username = cls._ParseStringOption(options, u'username')
    if not username:
      username = cls._DEFAULT_USERNAME

    password = cls._ParseStringOption(options, u'password')
    if not password:
      password = cls._DEFAULT_PASSWORD

    name = cls._ParseStringOption(options, u'db_name')
    if not name:
      name = cls._DEFAULT_NAME

    output_module.SetCredentials(username=username, password=password)
    output_module.SetDatabaseName(name)
    server_config.BaseServerConfigHelper.ParseOptions(options, output_module)
