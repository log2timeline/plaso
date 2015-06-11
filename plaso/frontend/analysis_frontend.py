# -*- coding: utf-8 -*-
"""The analysis front-end."""

from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import frontend
from plaso.lib import storage


class AnalysisFrontend(frontend.Frontend):
  """Class that implements an analysis front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    super(AnalysisFrontend, self).__init__()
    self._data_location = None

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

  def SetDataLocation(self, data_location):
    """Set the data location.

    Args:
      data_location: The path to the location that data files should be loaded
                     from.
    """
    self._data_location = data_location
