# -*- coding: utf-8 -*-
"""The 4n6time SQLite database output module CLI arguments helper."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import shared_4n6time_output
from plaso.cli.helpers import manager
from plaso.output import sqlite_4n6time


class SQLite4n6TimeOutputArgumentsHelper(interface.ArgumentsHelper):
  """4n6time SQLite database output module CLI arguments helper."""

  NAME = '4n6time_sqlite'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the 4n6Time SQLite output module.'

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

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when the output filename was not provided.
    """
    if not isinstance(output_module, sqlite_4n6time.SQLite4n6TimeOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of SQLite4n6TimeOutputModule')

    shared_4n6time_output.Shared4n6TimeOutputArgumentsHelper.ParseOptions(
        options, output_module)

    filename = getattr(options, 'write', None)
    if not filename:
      raise errors.BadConfigOption(
          'Output filename was not provided use "-w filename" to specify.')

    output_module.SetFilename(filename)


manager.ArgumentHelperManager.RegisterHelper(SQLite4n6TimeOutputArgumentsHelper)
