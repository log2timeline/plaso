# -*- coding: utf-8 -*-
"""Implements a StorageFile output module."""

from plaso.lib import event
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager
from plaso.storage import zip_file


class PlasoStorageOutputModule(interface.OutputModule):
  """Dumps event objects to a plaso storage file."""

  NAME = u'pstorage'
  DESCRIPTION = u'Dumps event objects to a plaso storage file.'

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(PlasoStorageOutputModule, self).__init__(output_mediator)
    self._file_path = None
    self._preprocessing_object = event.PreprocessObject()
    self._storage_file = None

  def Close(self):
    """Closes the plaso storage file."""
    self._storage_file.WritePreprocessObject(self._preprocessing_object)
    self._storage_file.Close()

  def Open(self):
    """Opens the plaso storage file."""
    self._preprocessing_object.collection_information = {
        u'time_of_run': timelib.Timestamp.GetNow()}

    filter_expression = self._output_mediator.filter_expression
    if filter_expression:
      self._preprocessing_object.collection_information[u'filter'] = (
          filter_expression)

    storage_file_path = self._output_mediator.storage_file_path
    if storage_file_path:
      self._preprocessing_object.collection_information[u'file_processed'] = (
          storage_file_path)

    self._storage_file = zip_file.StorageFile(self._file_path)

  def SetFilePath(self, file_path):
    """Sets the file-like object based on the file path.

    Args:
      file_path: the full path to the output file.
    """
    self._file_path = file_path

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    # Needed due to duplicate removals, if two events
    # are merged then we'll just pick the first inode value.
    inode = event_object.inode
    if isinstance(inode, py2to3.STRING_TYPES):
      inode_list = inode.split(u';')
      try:
        new_inode = int(inode_list[0])
      except (IndexError, ValueError):
        new_inode = 0

      event_object.inode = new_inode

    self._storage_file.AddEventObject(event_object)


manager.OutputManager.RegisterOutput(PlasoStorageOutputModule)
