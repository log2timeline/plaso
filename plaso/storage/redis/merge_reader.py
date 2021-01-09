# -*- coding: utf-8 -*-
"""Redis merge reader."""
import codecs

from plaso.lib import definitions
from plaso.storage import identifiers
from plaso.storage import interface
from plaso.storage import logger
from plaso.storage.redis import redis_store


class RedisMergeReader(interface.StorageMergeReader):
  """Redis store reader for merging."""

  def __init__(self, storage_writer, task, redis_client=None):
    """Initializes a Redis storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      task (Task): the task whose store is being merged.
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created.

    Raises:
      RuntimeError: if an add container method is missing.
    """
    super(RedisMergeReader, self).__init__(storage_writer)
    self._active_container_type = None
    self._container_types = []
    self._active_cursor = 0
    self._add_active_container_method = None
    self._store = redis_store.RedisStore(
        definitions.STORAGE_TYPE_TASK,
        session_identifier=task.session_identifier,
        task_identifier=task.identifier)
    self._store.Open(redis_client=redis_client)
    self._event_data_identifier_mappings = {}
    self._event_data_stream_identifier_mappings = {}
    self._add_container_type_methods = {}
    self._active_extra_containers = []

    # Create a runtime lookup table for the add container type method. This
    # prevents having to create a series of if-else checks for container types.
    # The table is generated at runtime as there are no forward function
    # declarations in Python.
    for container_type, method_name in self._ADD_CONTAINER_TYPE_METHODS.items():
      method = getattr(self, method_name, None)
      if not method:
        raise RuntimeError(
            'Add method missing for container type: {0:s}'.format(
                container_type))

      self._add_container_type_methods[container_type] = method

  def _AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): event.
      serialized_data (Optional[bytes]): serialized form of the event.
    """
    if hasattr(event, 'event_data_row_identifier'):
      event_data_identifier = identifiers.SQLTableIdentifier(
          self._CONTAINER_TYPE_EVENT_DATA,
          event.event_data_row_identifier)
      lookup_key = event_data_identifier.CopyToString()

      event_data_identifier = self._event_data_identifier_mappings[lookup_key]
      event.SetEventDataIdentifier(event_data_identifier)

    # TODO: add event identifier mappings for event tags.

    self._storage_writer.AddEvent(event, serialized_data=serialized_data)

  def _AddEventData(self, event_data, serialized_data=None):
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (bytes): serialized form of the event data.
    """
    row_identifier = getattr(
        event_data, '_event_data_stream_row_identifier', None)
    if row_identifier is not None:
      event_data_stream_identifier = identifiers.SQLTableIdentifier(
          self._CONTAINER_TYPE_EVENT_DATA_STREAM, row_identifier)
      lookup_key = event_data_stream_identifier.CopyToString()

      event_data_stream_identifier = (
          self._event_data_stream_identifier_mappings.get(lookup_key, None))

      if event_data_stream_identifier:
        event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)

    identifier = event_data.GetIdentifier()
    lookup_key = identifier.CopyToString()

    self._storage_writer.AddEventData(
        event_data, serialized_data=serialized_data)

    last_write_identifier = event_data.GetIdentifier()
    self._event_data_identifier_mappings[lookup_key] = last_write_identifier

  def _AddEventDataStream(self, event_data_stream, serialized_data=None):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
      serialized_data (bytes): serialized form of the event data stream.
    """
    identifier = event_data_stream.GetIdentifier()
    lookup_key = identifier.CopyToString()

    self._storage_writer.AddEventDataStream(
        event_data_stream, serialized_data=serialized_data)

    identifier = event_data_stream.GetIdentifier()
    self._event_data_stream_identifier_mappings[lookup_key] = identifier

  def _PrepareForNextContainerType(self):
    """Prepares for the next container type.

    This method prepares the task storage for merging the next container type.
    It sets the active container type, its add method and active cursor
    accordingly.
    """
    self._active_container_type = self._container_types.pop(0)

    self._add_active_container_method = self._add_container_type_methods.get(
        self._active_container_type)

    self._active_cursor = 0

  def _GetContainerTypes(self):
    """Retrieves the container types to merge.

    Container types not defined in _CONTAINER_TYPES are ignored and not merged.

    Specific container types reference other container types, such
    as event referencing event data. The names are ordered to ensure the
    attribute containers are merged in the correct order.

    Returns:
      list[str]: names of the container types to merge.
    """
    container_types = []
    for container_type in self._CONTAINER_TYPES:
      # pylint: disable=protected-access
      if self._store._HasAttributeContainers(container_type):
        container_types.append(container_type)
    return container_types

  def _GetAttributeContainers(
      self, container_type, callback=None, cursor=0, maximum_number_of_items=0):
    """Retrieves attribute containers of the specified type.

    Args:
      container_type (str): attribute container type.
      callback (function[StorageWriter, AttributeContainer]): function to call
          after each attribute container is deserialized.
      cursor (int): Redis cursor for scanning items.
      maximum_number_of_items (Optional[int]): maximum number of
          containers to retrieve, where 0 represent no limit.

    Returns:
      list(AttributeContainer): attribute containers from Redis.
    """
    if not cursor:
      cursor = 0

    cursor, items = self._store.GetSerializedAttributeContainers(
        container_type, cursor, maximum_number_of_items)

    containers = []
    identifiers_to_delete = []
    for identifier_bytes, serialized_container in items.items():
      identifier_string = codecs.decode(identifier_bytes, 'utf-8')
      identifier = identifiers.RedisKeyIdentifier(identifier_string)
      identifiers_to_delete.append(identifier)

      container = self._DeserializeAttributeContainer(
          self._active_container_type, serialized_container)
      container.SetIdentifier(identifier)

      if callback:
        callback(self._storage_writer, container)

      containers.append(container)

    self._store.RemoveAttributeContainers(container_type, identifiers_to_delete)

    self._active_cursor = cursor
    containers = self._active_extra_containers + containers

    if maximum_number_of_items:
      self._active_extra_containers = containers[maximum_number_of_items:]

    return containers[:maximum_number_of_items]

  def MergeAttributeContainers(
      self, callback=None, maximum_number_of_containers=0):
    """Reads attribute containers from a task store into the writer.

    Args:
      callback (Optional[function[StorageWriter, AttributeContainer]]): function
          to call after each attribute container is deserialized.
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      bool: True if the entire task storage file has been merged.

    Raises:
      RuntimeError: if the add method for the active attribute container
          type is missing.
    """
    if not self._container_types:
      self._container_types = self._GetContainerTypes()

    number_of_containers = 0
    while (self._active_cursor or self._container_types
           or self._active_extra_containers):
      if not self._active_cursor and not self._active_extra_containers:
        self._PrepareForNextContainerType()

      containers = self._GetAttributeContainers(
          self._active_container_type, callback=callback,
          cursor=self._active_cursor,
          maximum_number_of_items=maximum_number_of_containers)

      if not containers:
        self._active_cursor = 0
        continue

      for container in containers:
        self._add_active_container_method(container)
        number_of_containers += 1

      if 0 < maximum_number_of_containers <= number_of_containers:
        logger.debug(
            'Only merged {0:d} containers'.format(number_of_containers))
        return False

    logger.debug('Merged {0:d} containers'.format(number_of_containers))
    # While all the containers have been merged, the 'merging' key is still
    # present, so we still need to remove the store.
    self._store.Remove()
    return True
