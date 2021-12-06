# -*- coding: utf-8 -*-
"""Redis store.

Only supports task storage at the moment.
"""

import uuid

import redis

from plaso.containers import events
from plaso.lib import definitions
from plaso.storage import identifiers
from plaso.storage import interface
from plaso.storage import logger


class RedisStore(interface.BaseStore):
  """Redis store.

  Attribute containers are stored as Redis Hashes.
  All keys are prefixed with the session identifier to avoid collisions.
  Event identifiers are also stored in an index to enable sorting.
  """

  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE

  _FORMAT_VERSION = '20181013'
  _EVENT_INDEX_NAME = 'sorted_event_identifier'

  DEFAULT_REDIS_URL = 'redis://127.0.0.1/0'

  def __init__(self):
    """Initializes a Redis store."""
    super(RedisStore, self).__init__()
    self._redis_client = None
    self._session_identifier = None
    self._task_identifier = None

    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON

  def _GetRedisHashName(self, container_type):
    """Retrieves the Redis hash name of the attribute container type.

    Args:
      container_type (str): container type.

    Returns:
      str: a Redis key name.
    """
    return '{0:s}-{1:s}-{2:s}'.format(
        self._session_identifier, self._task_identifier, container_type)

  def _RaiseIfNotReadable(self):
    """Checks that the store is ready to for reading.

     Raises:
       IOError: if the store cannot be read from.
       OSError: if the store cannot be read from.
    """
    if not self._redis_client:
      raise IOError('Unable to read, client not connected.')

  def _RaiseIfNotWritable(self):
    """Checks that the store is ready to for writing.

    Raises:
      IOError: if the store cannot be written to.
      OSError: if the store cannot be written to.
    """
    if not self._redis_client:
      raise IOError('Unable to write, client not connected.')

  @classmethod
  def _SetClientName(cls, redis_client, name):
    """Attempts to sets a Redis client name.

    This method ignores errors from the Redis server or exceptions
    indicating the method is missing, as setting the name is not a critical
    function, and it is not currently supported by the fakeredis test library.

    Args:
      redis_client (Redis): an open Redis client.
      name (str): name to set.
    """
    try:
      redis_client.client_setname(name)
    except redis.ResponseError as exception:
      logger.debug(
          'Unable to set redis client name: {0:s} with error: {1!s}'.format(
              name, exception))

  def _UpdateAttributeContainerAfterDeserialize(self, container):
    """Updates an attribute container after deserialization.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      ValueError: if an attribute container identifier is missing.
    """
    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      row_identifier = getattr(
          container, '_event_data_row_identifier', None)
      if row_identifier:
        event_data_identifier = identifiers.RedisKeyIdentifier(
            self._CONTAINER_TYPE_EVENT_DATA, row_identifier)
        container.SetEventDataIdentifier(event_data_identifier)

        delattr(container, '_event_data_row_identifier')

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      row_identifier = getattr(
          container, '_event_data_stream_row_identifier', None)
      if row_identifier:
        event_data_stream_identifier = identifiers.RedisKeyIdentifier(
            self._CONTAINER_TYPE_EVENT_DATA_STREAM, row_identifier)
        container.SetEventDataStreamIdentifier(event_data_stream_identifier)

        delattr(container, '_event_data_stream_row_identifier')

  def _UpdateAttributeContainerBeforeSerialize(self, container):
    """Updates an attribute container before serialization.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: if the attribute container identifier type is not supported.
      OSError: if the attribute container identifier type is not supported.
    """
    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      event_data_identifier = container.GetEventDataIdentifier()
      if event_data_identifier:
        if not isinstance(
            event_data_identifier, identifiers.RedisKeyIdentifier):
          raise IOError(
              'Unsupported event data identifier type: {0!s}'.format(
                  type(event_data_identifier)))

        setattr(container, '_event_data_row_identifier',
                event_data_identifier.sequence_number)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      event_data_stream_identifier = container.GetEventDataStreamIdentifier()
      if event_data_stream_identifier:
        if not isinstance(
            event_data_stream_identifier, identifiers.RedisKeyIdentifier):
          raise IOError(
              'Unsupported event data stream identifier type: {0!s}'.format(
                  type(event_data_stream_identifier)))

        setattr(container, '_event_data_stream_row_identifier',
                event_data_stream_identifier.sequence_number)

  def _WriteExistingAttributeContainer(self, container):
    """Writes an existing attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: if an unsupported identifier is provided or if the attribute
          container does not exist.
      RuntimeError: since this method is not implemented.
      OSError: if an unsupported identifier is provided or if the attribute
          container does not exist.
    """
    identifier = container.GetIdentifier()
    if not isinstance(identifier, identifiers.RedisKeyIdentifier):
      raise IOError(
          'Unsupported attribute container identifier type: {0!s}'.format(
              type(identifier)))

    redis_hash_name = self._GetRedisHashName(container.CONTAINER_TYPE)
    redis_key = identifier.CopyToString()

    self._UpdateAttributeContainerBeforeSerialize(container)

    serialized_data = self._SerializeAttributeContainer(container)
    self._redis_client.hset(
        redis_hash_name, key=redis_key, value=serialized_data)

  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """
    next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
        container.CONTAINER_TYPE)

    identifier = identifiers.RedisKeyIdentifier(
        container.CONTAINER_TYPE, next_sequence_number)
    container.SetIdentifier(identifier)

    redis_hash_name = self._GetRedisHashName(container.CONTAINER_TYPE)
    redis_key = identifier.CopyToString()

    self._UpdateAttributeContainerBeforeSerialize(container)

    serialized_data = self._SerializeAttributeContainer(container)
    self._redis_client.hsetnx(redis_hash_name, redis_key, serialized_data)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      index_name = self._GetRedisHashName(self._EVENT_INDEX_NAME)
      self._redis_client.zincrby(index_name, container.timestamp, redis_key)

  def _WriteStorageMetadata(self):
    """Writes the storage metadata."""
    metadata = {
        'format_version': self._FORMAT_VERSION,
        'serialization_format': self.serialization_format}
    metadata_key = self._GetRedisHashName('metadata')

    for key, value in metadata.items():
      self._redis_client.hset(metadata_key, key=key, value=value)

  def Close(self):
    """Closes the store.

    Raises:
      IOError: if the store is already closed.
      OSError: if the store is already closed.
    """
    if not self._redis_client:
      raise IOError('Store already closed.')

    self._redis_client = None

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (RedisKeyIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the store is closed or if an unsupported identifier is
          provided.
      OSError: when the store is closed or if an unsupported identifier is
          provided.
    """
    if not isinstance(identifier, identifiers.RedisKeyIdentifier):
      raise IOError(
          'Unsupported attribute container identifier type: {0!s}'.format(
              type(identifier)))

    redis_hash_name = self._GetRedisHashName(container_type)
    redis_key = identifier.CopyToString()

    serialized_data = self._redis_client.hget(redis_hash_name, redis_key)
    if not serialized_data:
      return None

    attribute_container = self._DeserializeAttributeContainer(
        container_type, serialized_data)

    attribute_container.SetIdentifier(identifier)

    self._UpdateAttributeContainerAfterDeserialize(attribute_container)

    return attribute_container

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    sequence_number = index + 1
    redis_hash_name = self._GetRedisHashName(container_type)
    redis_key = '{0:s}.{1:d}'.format(container_type, sequence_number)

    serialized_data = self._redis_client.hget(redis_hash_name, redis_key)
    if not serialized_data:
      return None

    attribute_container = self._DeserializeAttributeContainer(
        container_type, serialized_data)

    identifier = identifiers.RedisKeyIdentifier(container_type, sequence_number)
    attribute_container.SetIdentifier(identifier)

    self._UpdateAttributeContainerAfterDeserialize(attribute_container)

    return attribute_container

  def GetAttributeContainers(self, container_type, filter_expression=None):
    """Retrieves attribute containers

    Args:
      container_type (str): container type attribute of the container being
          added.
      filter_expression (Optional[str]): expression to filter the resulting
          attribute containers by.

    Yields:
      AttributeContainer: attribute container.
    """
    redis_hash_name = self._GetRedisHashName(container_type)
    for redis_key, serialized_data in self._redis_client.hscan_iter(
        redis_hash_name):
      redis_key = redis_key.decode('utf-8')

      attribute_container = self._DeserializeAttributeContainer(
          container_type, serialized_data)

      _, sequence_number = redis_key.split('.')
      sequence_number = int(sequence_number, 10)
      identifier = identifiers.RedisKeyIdentifier(
          container_type, sequence_number)
      attribute_container.SetIdentifier(identifier)

      self._UpdateAttributeContainerAfterDeserialize(attribute_container)

      # TODO: map filter expression to Redis native filter.
      if attribute_container.MatchesExpression(filter_expression):
        yield attribute_container

  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.
    """
    redis_hash_name = self._GetRedisHashName(container_type)
    return self._redis_client.hlen(redis_hash_name)

  def GetSerializedAttributeContainers(
      self, container_type, cursor, maximum_number_of_items):
    """Fetches serialized attribute containers.

    Args:
      container_type (str): attribute container type.
      cursor (int): Redis cursor.
      maximum_number_of_items (int): maximum number of containers to
          retrieve, where 0 represent no limit.

    Returns:
      tuple: containing:
        int: Redis cursor.
        list[bytes]: serialized attribute containers.
    """
    name = self._GetRedisHashName(container_type)
    # Redis treats None as meaning "no limit", not 0.
    if maximum_number_of_items == 0:
      maximum_number_of_items = None

    cursor, items = self._redis_client.hscan(
        name, cursor=cursor, count=maximum_number_of_items)
    return cursor, items

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): This argument is not supported by the
          Redis store.

    Yields:
      EventObject: event.

    Raises:
      RuntimeError: if a time_range argument is specified.
    """
    event_index_name = self._GetRedisHashName(self._EVENT_INDEX_NAME)
    if time_range:
      raise RuntimeError('Not supported')

    for redis_key, _ in self._redis_client.zscan_iter(event_index_name):
      redis_key = redis_key.decode('utf-8')

      container_type, sequence_number = redis_key.split('.')
      sequence_number = int(sequence_number, 10)
      identifier = identifiers.RedisKeyIdentifier(
          container_type, sequence_number)
      yield self.GetAttributeContainerByIdentifier(
          self._CONTAINER_TYPE_EVENT, identifier)

  def HasAttributeContainers(self, container_type):
    """Determines if the store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    redis_hash_name = self._GetRedisHashName(container_type)
    number_of_containers = self._redis_client.hlen(redis_hash_name)
    return number_of_containers > 0

  # pylint: disable=arguments-differ
  def Open(
      self, redis_client=None, session_identifier=None, task_identifier=None,
      url=None, **unused_kwargs):
    """Opens the store.

    Args:
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created. If no client is specified a new client
          will be opened connected to the Redis instance specified by 'url'.
      session_identifier (Optional[str]): identifier of the session.
      task_identifier (Optional[str]): unique identifier of the task the store
          will store containers for. If not specified, an identifier will be
          generated.
      url (Optional[str]): URL for a Redis database. If not specified, the
          DEFAULT_REDIS_URL will be used.

    Raises:
      IOError: if the store is already connected to a Redis instance.
      OSError: if the store is already connected to a Redis instance.
    """
    if self._redis_client:
      raise IOError('Redis client already connected')

    if not redis_client:
      if not url:
        url = self.DEFAULT_REDIS_URL

      redis_client = redis.from_url(url=url, socket_timeout=60)

    self._redis_client = redis_client

    self._session_identifier = session_identifier or str(uuid.uuid4())
    self._task_identifier = task_identifier or str(uuid.uuid4())

    client_name = self._GetRedisHashName('')
    self._SetClientName(self._redis_client, client_name)

    metadata_key = self._GetRedisHashName('metadata')
    if not self._redis_client.exists(metadata_key):
      self._WriteStorageMetadata()
