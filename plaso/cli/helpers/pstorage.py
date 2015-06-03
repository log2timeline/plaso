# -*- coding: utf-8 -*-
"""The arguments helper for the pstorage output module."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import pstorage


class PstorageOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for a pstorage output module."""

  NAME = u'pstorage'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the pstorage output module.'

  @classmethod
  def AddArguments(cls, unused_argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
    """
    pass

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
    if not isinstance(output_module, pstorage.PlasoStorageOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of PlasoStorageOutputModule.')

    file_path = getattr(options, u'write', None)
    if file_path:
      output_module.SetFilehandle(file_path=file_path)


manager.ArgumentHelperManager.RegisterHelper(PstorageOutputHelper)
