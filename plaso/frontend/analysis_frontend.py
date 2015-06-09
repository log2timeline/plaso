# -*- coding: utf-8 -*-
"""The analysis front-end."""

import os

from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import frontend
from plaso.lib import errors
from plaso.lib import storage


class AnalysisFrontend(frontend.Frontend):
  """Class that implements an analysis front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    super(AnalysisFrontend, self).__init__()
    self._data_location = None
    self._storage_file_path = None

  def AddStorageFileOptions(self, argument_group):
    """Adds the storage file options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup) or argument parser (instance of
                      argparse.ArgumentParser).
    """
    argument_group.add_argument(
        u'storage_file', metavar=u'STORAGE_FILE', action=u'store', nargs=u'?',
        type=unicode, default=None, help=u'The path of the storage file.')

  def GetFormatterMediator(self):
    """Retrieves the formatter mediator.

    Returns:
      The formatter mediator (instance of FormatterMediator).
    """
    return formatters_mediator.FormatterMediator(
        data_location=self._data_location)

  # TODO: refactor to pass storage options.
  def OpenStorage(self, storage_file_path, read_only=True):
    """Opens the storage.

    Args:
      storage_file_path: the path of the storage file.
      read_only: optional boolean value to indicate the storage file should
                 be opened in read-only mode. The default is True.

    Returns:
      The storage file object (instance of StorageFile).
    """
    return storage.StorageFile(storage_file_path, read_only=read_only)

  def OpenStorageFile(self, read_only=True):
    """Opens the storage file.

    Args:
      read_only: optional boolean value to indicate the storage file should
                 be opened in read-only mode. The default is True.

    Returns:
      The storage file object (instance of StorageFile).
    """
    return storage.StorageFile(self._storage_file_path, read_only=read_only)

  # TODO: Frontends should not have any option parsing code in them. Refactor to
  # remove this.
  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    if not options:
      raise errors.BadConfigOption(u'Missing options.')

    self._storage_file_path = getattr(options, 'storage_file', None)
    if not self._storage_file_path:
      raise errors.BadConfigOption(u'Missing storage file.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          u'No such storage file {0:s}.'.format(self._storage_file_path))

  def SetDataLocation(self, data_location):
    """Set the data location.

    Args:
      data_location: The path to the location that data files should be loaded
                     from.
    """
    self._data_location = data_location
