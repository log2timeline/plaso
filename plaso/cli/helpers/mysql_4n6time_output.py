# -*- coding: utf-8 -*-
"""The arguments helper for the 4n6time MySQL database output module."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import database_config
from plaso.cli.helpers import shared_4n6time_output
from plaso.cli.helpers import manager
from plaso.output import mysql_4n6time


class MySQL4n6TimeHelper(database_config.DatabaseConfigHelper):
  """CLI argument helper for a 4n6Time MySQL database server."""

  _DEFAULT_USERNAME = u'root'
  _DEFAULT_PASSWORD = u'forensic'


class MySQL4n6TimeOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for a MySQL 4n6time output module."""

  NAME = u'4n6time_mysql'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the 4n6Time MySQL output module.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
    """
    shared_4n6time_output.Shared4n6TimeOutputHelper.AddArguments(argument_group)
    MySQL4n6TimeHelper.AddArguments(argument_group)

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(output_module, mysql_4n6time.MySQL4n6TimeOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of MySQL4n6TimeOutputModule')

    MySQL4n6TimeHelper.ParseOptions(options, output_module)
    shared_4n6time_output.Shared4n6TimeOutputHelper.ParseOptions(
        options, output_module)


manager.ArgumentHelperManager.RegisterHelper(MySQL4n6TimeOutputHelper)
