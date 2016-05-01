# -*- coding: utf-8 -*-
"""The storage writer objects."""

from plaso.engine import plaso_queue
from plaso.lib import definitions


class StorageWriter(plaso_queue.ItemQueueConsumer):
  """Class that defines the storage writer interface."""

  # pylint: disable=abstract-method
  # Have pylint ignore that we are not overriding _ConsumeItem.

  def __init__(self, event_object_queue):
    """Initializes a storage writer object.

    Args:
      event_object_queue: the event object queue (instance of Queue).
    """
    super(StorageWriter, self).__init__(event_object_queue)

    # Attributes that contain the current status of the storage writer.
    self._status = definitions.PROCESSING_STATUS_INITIALIZED

    # Attributes for profiling.
    self._enable_profiling = False
    self._profiling_type = u'all'

    self.number_of_event_sources = 0

  def AddEventSource(self, unused_event_source):
    """Adds an event source to the storage.

    Args:
      event_source: an event source object (instance of EventSource).
    """
    self.number_of_event_sources += 1

  def Close(self):
    """Closes the storage writer."""
    return

  def GetStatus(self):
    """Returns a dictionary containing the status."""
    return {
        u'number_of_events': self.number_of_consumed_items,
        u'processing_status': self._status,
        u'type': definitions.PROCESS_TYPE_STORAGE_WRITER}

  def Open(self):
    """Opens the storage writer."""
    return

  def SetEnableProfiling(self, enable_profiling, profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if profiling should
                        be enabled.
      profiling_type: optional profiling type.
    """
    self._enable_profiling = enable_profiling
    self._profiling_type = profiling_type

  def WriteEventObjects(self):
    """Writes the event objects that are pushed on the queue."""
    self._status = definitions.PROCESSING_STATUS_RUNNING

    self.Open()
    self.ConsumeItems()
    self.Close()

    self._status = definitions.PROCESSING_STATUS_COMPLETED
