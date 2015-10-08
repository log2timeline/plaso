# -*- coding: utf-8 -*-
"""The arguments helper for the 4n6time SQLite database output module."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import shared_4n6time_output
from plaso.cli.helpers import manager
from plaso.output import sqlite_4n6time


class SQLite4n6TimeOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for a SQLite 4n6time output module."""

  NAME = u'4n6time_sqlite'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the 4n6Time SQLite output module.'

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

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(output_module, sqlite_4n6time.SQLite4n6TimeOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of SQLite4n6TimeOutputModule')

    shared_4n6time_output.Shared4n6TimeOutputHelper.ParseOptions(
        options, output_module)

    filename = getattr(options, u'write', None)
    if filename:
      output_module.SetFilename(filename)


manager.ArgumentHelperManager.RegisterHelper(SQLite4n6TimeOutputHelper)
