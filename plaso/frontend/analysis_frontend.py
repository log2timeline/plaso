# -*- coding: utf-8 -*-
"""The analysis front-end."""

from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import frontend
from plaso.storage import zip_file as storage_zip_file


class AnalysisFrontend(frontend.Frontend):
  """Class that implements an analysis front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    super(AnalysisFrontend, self).__init__()
    self._data_location = None
    self._storage_file = None

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
    return storage_zip_file.StorageFile(storage_file_path, read_only=read_only)

  def SetDataLocation(self, data_location):
    """Set the data location.

    Args:
      data_location: The path to the location that data files should be loaded
                     from.
    """
    self._data_location = data_location

  def SetStorageFile(self, storage_file):
    """Set the storage file.

    Args:
      storage_file: The path to the storage file being parsed.
    """
    self._storage_file = storage_file
