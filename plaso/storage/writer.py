# -*- coding: utf-8 -*-
"""The storage writer objects."""

import abc

from plaso.engine import plaso_queue
from plaso.lib import definitions


# TODO: remove queue consumer as the super class.
class StorageWriter(plaso_queue.ItemQueueConsumer):
  """Class that defines the storage writer interface.

  Attributes:
    number_of_event_sources: an integer containing the number of event
                             sources written.
  """

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

  @abc.abstractmethod
  def AddEventSource(self, event_source):
    """Adds an event source to the storage.

    Args:
      event_source: an event source object (instance of EventSource).
    """

  @abc.abstractmethod
  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      An event source object (instance of EventSource).
    """

  def GetStatus(self):
    """Returns a dictionary containing the status."""
    return {
        u'number_of_events': self.number_of_consumed_items,
        u'processing_status': self._status,
        u'type': definitions.PROCESS_TYPE_STORAGE_WRITER}

  def SetEnableProfiling(self, enable_profiling, profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if profiling should
                        be enabled.
      profiling_type: optional profiling type.
    """
    self._enable_profiling = enable_profiling
    self._profiling_type = profiling_type

  @abc.abstractmethod
  def WriteEventObjects(self):
    """Writes the event objects that are pushed on the queue."""
