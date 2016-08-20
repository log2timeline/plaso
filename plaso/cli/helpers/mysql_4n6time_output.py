# -*- coding: utf-8 -*-
"""The 4n6time MySQL database output module CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import database_config
from plaso.cli.helpers import shared_4n6time_output
from plaso.cli.helpers import manager
from plaso.output import mysql_4n6time


class MySQL4n6TimeDatabaseArgumentsHelper(
    database_config.DatabaseArgumentsHelper):
  """4n6time MySQL database server CLI arguments helper."""

  _DEFAULT_USERNAME = u'root'
  _DEFAULT_PASSWORD = u'forensic'


class MySQL4n6TimeOutputArgumentsHelper(interface.ArgumentsHelper):
  """4n6time MySQL database output module CLI arguments helper."""

  NAME = u'4n6time_mysql'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the 4n6Time MySQL output module.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    shared_4n6time_output.Shared4n6TimeOutputArgumentsHelper.AddArguments(
        argument_group)
    MySQL4n6TimeDatabaseArgumentsHelper.AddArguments(argument_group)

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(output_module, mysql_4n6time.MySQL4n6TimeOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of MySQL4n6TimeOutputModule')

    MySQL4n6TimeDatabaseArgumentsHelper.ParseOptions(options, output_module)
    shared_4n6time_output.Shared4n6TimeOutputArgumentsHelper.ParseOptions(
        options, output_module)


manager.ArgumentHelperManager.RegisterHelper(MySQL4n6TimeOutputArgumentsHelper)
