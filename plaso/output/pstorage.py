# -*- coding: utf-8 -*-
"""Implements a StorageFile output module."""

import sys

from plaso.lib import event
from plaso.lib import storage
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class PlasoStorageOutputModule(interface.OutputModule):
  """Dumps event objects to a plaso storage file."""

  NAME = u'pstorage'
  DESCRIPTION = u'Dumps event objects to a plaso storage file.'

  def __init__(self, output_mediator, filehandle=sys.stdout, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.

    Raises:
     TypeError: if the file handle is of an unsupported type.
    """
    super(PlasoStorageOutputModule, self).__init__(output_mediator, **kwargs)

    if isinstance(filehandle, basestring):
      self._file_object = open(filehandle, 'wb')

    # Check if the filehandle object has a write method.
    elif hasattr(filehandle, u'write'):
      self._file_object = filehandle

    else:
      raise TypeError(u'Unsupported file handle type.')

    self._storage = None

  def Close(self):
    """Closes the plaso storage file."""
    self._storage.Close()

  def Open(self):
    """Opens the plaso storage file."""
    pre_obj = event.PreprocessObject()
    pre_obj.collection_information = {
        u'time_of_run': timelib.Timestamp.GetNow()}

    configuration_value = self._output_mediator.GetConfigurationValue(u'filter')
    if configuration_value:
      pre_obj.collection_information[u'filter'] = configuration_value

    configuration_value = self._output_mediator.GetConfigurationValue(
        u'storagefile')
    if configuration_value:
      pre_obj.collection_information[u'file_processed'] = configuration_value

    self._storage = storage.StorageFile(self._file_object, pre_obj=pre_obj)

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    # Needed due to duplicate removals, if two events
    # are merged then we'll just pick the first inode value.
    inode = getattr(event_object, u'inode', None)
    if isinstance(inode, basestring):
      inode_list = inode.split(u';')
      try:
        new_inode = int(inode_list[0])
      except (ValueError, IndexError):
        new_inode = 0

      event_object.inode = new_inode

    self._storage.AddEventObject(event_object)


manager.OutputManager.RegisterOutput(PlasoStorageOutputModule)
