# -*- coding: utf-8 -*-
"""Implements a StorageFile output module."""

from plaso.lib import event
from plaso.lib import storage
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class PlasoStorageOutputFormatter(interface.OutputModule):
  """Dumps event objects to a plaso storage file."""

  NAME = u'pstorage'
  DESCRIPTION = u'Dumps event objects to a plaso storage file.'

  def Close(self):
    """Closes the plaso storage file."""
    self._storage.Close()

  def Open(self):
    """Opens the plaso storage file."""
    pre_obj = event.PreprocessObject()
    pre_obj.collection_information = {'time_of_run': timelib.Timestamp.GetNow()}
    if hasattr(self._config, 'filter') and self._config.filter:
      pre_obj.collection_information['filter'] = self._config.filter
    if hasattr(self._config, 'storagefile') and self._config.storagefile:
      pre_obj.collection_information[
          'file_processed'] = self._config.storagefile
    self._storage = storage.StorageFile(self._file_object, pre_obj=pre_obj)

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    # Needed due to duplicate removals, if two events
    # are merged then we'll just pick the first inode value.
    inode = getattr(event_object, 'inode', None)
    if isinstance(inode, basestring):
      inode_list = inode.split(';')
      try:
        new_inode = int(inode_list[0])
      except (ValueError, IndexError):
        new_inode = 0

      event_object.inode = new_inode

    self._storage.AddEventObject(event_object)


manager.OutputManager.RegisterOutput(PlasoStorageOutputFormatter)
