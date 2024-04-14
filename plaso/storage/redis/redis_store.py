# -*- coding: utf-8 -*-
"""Redis-based attribute container store.

Only supports task storage at the moment.
"""

import ast
import json
import uuid

import redis  # pylint: disable=import-error

from acstore import interface
from acstore.containers import interface as containers_interface
from acstore.helpers import json_serializer as containers_json_serializer

from plaso.containers import events
from plaso.lib import definitions
from plaso.serializer import json_serializer
from plaso.storage import logger


class BaseRedisAttributeContainerStore(
    interface.AttributeContainerStoreWithReadCache):
  """Redis-based attribute container store.

  Attribute containers are stored as Redis hashes. All keys are prefixed with
  the session identifier to avoid collisions. Event identifiers are also stored
  in an index to enable sorting.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
  """

  _FORMAT_VERSION = 20230312

  DEFAULT_REDIS_URL = 'redis://127.0.0.1/0'

  def __init__(self):
    """Initializes a Redis attribute container store."""
    super(BaseRedisAttributeContainerStore, self).__init__()
    self._json_serializer = (
        containers_json_serializer.AttributeContainerJSONSerializer)
    self._redis_client = None
    self._session_identifier = None
    self._task_identifier = None

    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON

  def _GetRedisHashName(self, container_type):
    """Retrieves the Redis hash name of the attribute container type.

    Args:
      container_type (str): container type.

    Returns:
      str: a Redis key name.
    """
    return (f'{self._session_identifier:s}-{self._task_identifier:s}-'
            f'{container_type:s}')

  def _RaiseIfNotReadable(self):
    """Raises if the attribute container store is not readable.

    Raises:
      IOError: when the attribute container store is closed.
      OSError: when the attribute container store is closed.
    """
    if not self._redis_client:
      raise IOError('Unable to read, client not connected.')

  def _RaiseIfNotWritable(self):
    """Raises if the attribute container store is not writable.

    Raises:
      IOError: when the attribute container store is closed or read-only.
      OSError: when the attribute container store is closed or read-only.
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
      logger.debug((
          f'Unable to set redis client name: {name:s} with error: '
          f'{exception!s}'))

  def _WriteExistingAttributeContainer(self, container):
    """Writes an existing attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """
    identifier = container.GetIdentifier()

    redis_hash_name = self._GetRedisHashName(container.CONTAINER_TYPE)
    redis_key = identifier.CopyToString()

    json_dict = self._json_serializer.ConvertAttributeContainerToJSON(container)

    try:
      json_string = json.dumps(json_dict)
    except TypeError as exception:
      raise IOError((
          f'Unable to serialize attribute container: '
          f'{container.CONTAINER_TYPE:s} with error: {exception!s}.'))

    if not json_string:
      raise IOError((
          f'Unable to serialize attribute container: '
          f'{container.CONTAINER_TYPE:s}'))

    self._redis_client.hset(redis_hash_name, key=redis_key, value=json_string)

  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """
    next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
        container.CONTAINER_TYPE)

    identifier = containers_interface.AttributeContainerIdentifier(
        name=container.CONTAINER_TYPE, sequence_number=next_sequence_number)
    container.SetIdentifier(identifier)

    redis_hash_name = self._GetRedisHashName(container.CONTAINER_TYPE)
    redis_key = identifier.CopyToString()

    json_dict = self._json_serializer.ConvertAttributeContainerToJSON(container)

    try:
      json_string = json.dumps(json_dict)
    except TypeError as exception:
      raise IOError((
          f'Unable to serialize attribute container: '
          f'{container.CONTAINER_TYPE:s} with error: {exception!s}.'))

    if not json_string:
      raise IOError((
          f'Unable to serialize attribute container: '
          f'{container.CONTAINER_TYPE:s}'))

    self._redis_client.hsetnx(redis_hash_name, redis_key, json_string)

    self._CacheAttributeContainerByIndex(container, next_sequence_number - 1)

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
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    redis_hash_name = self._GetRedisHashName(container_type)
    redis_key = identifier.CopyToString()

    json_string = self._redis_client.hget(redis_hash_name, redis_key)
    if not json_string:
      return None

    json_dict = json.loads(json_string)

    container = self._json_serializer.ConvertJSONToAttributeContainer(json_dict)
    container.SetIdentifier(identifier)
    return container

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    identifier = containers_interface.AttributeContainerIdentifier(
        name=container_type, sequence_number=index + 1)

    redis_hash_name = self._GetRedisHashName(container_type)
    redis_key = identifier.CopyToString()

    json_string = self._redis_client.hget(redis_hash_name, redis_key)
    if not json_string:
      return None

    json_dict = json.loads(json_string)

    container = self._json_serializer.ConvertJSONToAttributeContainer(json_dict)
    container.SetIdentifier(identifier)
    return container

  def GetAttributeContainers(self, container_type, filter_expression=None):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.
      filter_expression (Optional[str]): expression to filter the resulting
          attribute containers by.

    Yields:
      AttributeContainer: attribute container.
    """
    redis_hash_name = self._GetRedisHashName(container_type)

    if filter_expression:
      expression_ast = ast.parse(filter_expression, mode='eval')
      filter_expression = compile(expression_ast, '<string>', mode='eval')

    for redis_key, json_string in self._redis_client.hscan_iter(
        redis_hash_name):
      json_dict = json.loads(json_string)

      container = self._json_serializer.ConvertJSONToAttributeContainer(
          json_dict)
      # TODO: map filter expression to Redis native filter.
      if container.MatchesExpression(filter_expression):
        key = redis_key.decode('utf8')
        identifier = containers_interface.AttributeContainerIdentifier()
        identifier.CopyFromString(key)

        container.SetIdentifier(identifier)
        yield container

  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.
    """
    redis_hash_name = self._GetRedisHashName(container_type)
    return self._redis_client.hlen(redis_hash_name)

  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    return self._attribute_container_sequence_numbers[container_type] > 0

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


class RedisAttributeContainerStore(BaseRedisAttributeContainerStore):
  """Redis-based attribute container store.

  Attribute containers are stored as Redis hashes. All keys are prefixed with
  the session identifier to avoid collisions. Event identifiers are also stored
  in an index to enable sorting.
  """

  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE

  _EVENT_INDEX_NAME = 'sorted_event_identifier'

  def __init__(self):
    """Initializes a Redis attribute container store."""
    super(RedisAttributeContainerStore, self).__init__()
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializers_profiler = None

  def _DeserializeAttributeContainer(self, container_type, serialized_data):
    """Deserializes an attribute container.

    Args:
      container_type (str): attribute container type.
      serialized_data (bytes): serialized attribute container data.

    Returns:
      AttributeContainer: attribute container or None.

    Raises:
      IOError: if the serialized data cannot be decoded.
      OSError: if the serialized data cannot be decoded.
    """
    if not serialized_data:
      return None

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(container_type)

    try:
      serialized_string = serialized_data.decode('utf-8')
      attribute_container = self._serializer.ReadSerialized(serialized_string)

    except UnicodeDecodeError as exception:
      raise IOError(
          f'Unable to decode serialized data with error: {exception!s}')

    except (TypeError, ValueError) as exception:
      # TODO: consider re-reading attribute container with error correction.
      raise IOError(f'Unable to read serialized data with error: {exception!s}')

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(container_type)

    return attribute_container

  def _SerializeAttributeContainer(self, attribute_container):
    """Serializes an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      bytes: serialized attribute container.

    Raises:
      IOError: if the attribute container cannot be serialized.
      OSError: if the attribute container cannot be serialized.
    """
    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(
          attribute_container.CONTAINER_TYPE)

    try:
      attribute_container_data = self._serializer.WriteSerialized(
          attribute_container)
      if not attribute_container_data:
        raise IOError((
            f'Unable to serialize attribute container: '
            f'{attribute_container.CONTAINER_TYPE:s}'))

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(
            attribute_container.CONTAINER_TYPE)

    return attribute_container_data

  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """
    schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)
    if schema:
      super(RedisAttributeContainerStore, self)._WriteNewAttributeContainer(
          container)
    else:
      next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
          container.CONTAINER_TYPE)

      identifier = containers_interface.AttributeContainerIdentifier(
          name=container.CONTAINER_TYPE, sequence_number=next_sequence_number)
      container.SetIdentifier(identifier)

      redis_hash_name = self._GetRedisHashName(container.CONTAINER_TYPE)
      redis_key = identifier.CopyToString()

      if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
        event_data_stream_identifier = container.GetEventDataStreamIdentifier()
        if event_data_stream_identifier:
          setattr(container, '_event_data_stream_identifier',
                  event_data_stream_identifier.sequence_number)

      serialized_data = self._SerializeAttributeContainer(container)
      self._redis_client.hsetnx(redis_hash_name, redis_key, serialized_data)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      index_name = self._GetRedisHashName(self._EVENT_INDEX_NAME)

      identifier = container.GetIdentifier()
      redis_key = identifier.CopyToString()

      self._redis_client.zincrby(index_name, container.timestamp, redis_key)

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    schema = self._GetAttributeContainerSchema(container_type)
    if schema:
      return super(
          RedisAttributeContainerStore, self).GetAttributeContainerByIndex(
              container_type, index)

    identifier = containers_interface.AttributeContainerIdentifier(
        name=container_type, sequence_number=index + 1)

    redis_hash_name = self._GetRedisHashName(container_type)
    redis_key = identifier.CopyToString()

    serialized_data = self._redis_client.hget(redis_hash_name, redis_key)
    if not serialized_data:
      return None

    container = self._DeserializeAttributeContainer(
        container_type, serialized_data)
    container.SetIdentifier(identifier)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      identifier = getattr(container, '_event_data_stream_identifier', None)
      if identifier:
        event_data_stream_identifier = (
            containers_interface.AttributeContainerIdentifier(
                name=self._CONTAINER_TYPE_EVENT_DATA_STREAM,
                sequence_number=identifier))
        container.SetEventDataStreamIdentifier(event_data_stream_identifier)

    return container

  def GetAttributeContainers(self, container_type, filter_expression=None):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.
      filter_expression (Optional[str]): expression to filter the resulting
          attribute containers by.

    Yields:
      AttributeContainer: attribute container.
    """
    schema = self._GetAttributeContainerSchema(container_type)
    if schema:
      yield from super(
          RedisAttributeContainerStore, self).GetAttributeContainers(
              container_type, filter_expression=filter_expression)
    else:
      redis_hash_name = self._GetRedisHashName(container_type)
      for redis_key, serialized_data in self._redis_client.hscan_iter(
          redis_hash_name):
        container = self._DeserializeAttributeContainer(
            container_type, serialized_data)

        redis_key = redis_key.decode('utf-8')
        identifier = containers_interface.AttributeContainerIdentifier()
        identifier.CopyFromString(redis_key)

        if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
          identifier = getattr(container, '_event_data_stream_identifier', None)
          if identifier:
            event_data_stream_identifier = (
                containers_interface.AttributeContainerIdentifier(
                    name=self._CONTAINER_TYPE_EVENT_DATA_STREAM,
                    sequence_number=identifier))
            container.SetEventDataStreamIdentifier(event_data_stream_identifier)

        # TODO: map filter expression to Redis native filter.
        if container.MatchesExpression(filter_expression):
          yield container

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
      identifier = containers_interface.AttributeContainerIdentifier()
      identifier.CopyFromString(redis_key)

      yield self.GetAttributeContainerByIdentifier(
          self._CONTAINER_TYPE_EVENT, identifier)

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler
