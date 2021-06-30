# -*- coding: utf-8 -*-
"""Fake (in-memory only) store for testing."""

import collections
import copy
import itertools

from plaso.lib import definitions
from plaso.storage import event_heaps
from plaso.storage import identifiers
from plaso.storage import interface


class FakeStore(interface.BaseStore):
  """Fake (in-memory only) store for testing."""

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a fake (in-memory only) store.

    Args:
      storage_type (Optional[str]): storage type.
    """
    super(FakeStore, self).__init__(storage_type=storage_type)
    self._attribute_containers = {}
    self._attribute_container_sequence_numbers = collections.Counter()
    self._is_open = False

  def _GetAttributeContainerNextSequenceNumber(self, container_type):
    """Retrieves the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: next sequence number.
    """
    self._attribute_container_sequence_numbers[container_type] += 1
    return self._attribute_container_sequence_numbers[container_type]

  def _RaiseIfNotReadable(self):
    """Raises if the store is not readable.

     Raises:
       OSError: if the store cannot be read from.
       IOError: if the store cannot be read from.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed storage writer.')

  def _RaiseIfNotWritable(self):
    """Raises if the storage file is not writable.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed storage writer.')

  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """
    containers = self._attribute_containers.get(container.CONTAINER_TYPE, None)
    if containers is None:
      containers = collections.OrderedDict()
      self._attribute_containers[container.CONTAINER_TYPE] = containers

    next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
        container.CONTAINER_TYPE)

    identifier = identifiers.FakeIdentifier(next_sequence_number)
    container.SetIdentifier(identifier)

    lookup_key = identifier.CopyToString()

    # Make sure the fake storage preserves the state of the attribute container.
    container = copy.deepcopy(container)
    containers[lookup_key] = container

    # TODO: maintain a mapping of event identifier to tag.

  def Close(self):
    """Closes the store.

    Raises:
      IOError: if the store is already closed.
      OSError: if the store is already closed.
    """
    if not self._is_open:
      raise IOError('Store already closed.')

    self._is_open = False

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    containers = self._attribute_containers.get(container_type, {})

    lookup_key = identifier.CopyToString()
    return containers.get(lookup_key, None)

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    containers = self._attribute_containers.get(container_type, {})
    number_of_containers = len(containers)
    if index < 0 or index >= number_of_containers:
      return None

    return next(itertools.islice(
        containers.values(), index, number_of_containers))

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    containers = self._attribute_containers.get(container_type, {})
    return iter(containers.values())

  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.
    """
    containers = self._attribute_containers.get(container_type, {})
    return len(containers)

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage writer.')

    generator = self.GetAttributeContainers(self._CONTAINER_TYPE_EVENT)
    event_heap = event_heaps.EventHeap()

    for event_index, event in enumerate(generator):
      if (time_range and (
          event.timestamp < time_range.start_timestamp or
          event.timestamp > time_range.end_timestamp)):
        continue

      # The event index is used to ensure to sort events with the same date and
      # time and description in the order they were added to the store.
      event_heap.PushEvent(event, event_index)

    return iter(event_heap.PopEvents())

  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    containers = self._attribute_containers.get(container_type, {})
    return bool(containers)

  def Open(self, **kwargs):
    """Opens the store.

    Raises:
      IOError: if the store is already opened.
      OSError: if the store is already opened.
    """
    if self._is_open:
      raise IOError('Store already opened.')

    self._is_open = True
