# -*- coding: utf-8 -*-
"""Redis store.

Only supports task storage at the moment.
"""
from __future__ import unicode_literals

import uuid

import redis

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

  _FORMAT_VERSION = '20181013'
  _EVENT_INDEX_NAME = 'sorted_event_identifier'
  _FINALIZED_KEY_NAME = 'finalized'
  _FINALIZED_BYTES = b'finalized'
  _MERGING_KEY_NAME = 'merging'
  _MERGING_BYTES = b'merging'
  # DEFAULT_REDIS_URL is public so that it appears in generated documentation.
  DEFAULT_REDIS_URL = 'redis://127.0.0.1/0'

  def __init__(
      self, storage_type=definitions.STORAGE_TYPE_TASK,
      session_identifier=None, task_identifier=None):
    """Initializes a Redis store.

    Args:
      storage_type (Optional[str]): storage type.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
      task_identifier (Optional[str]): unique identifier of the task the store
          will store containers for. If not specified, an identifier will be
          generated.

    Raises:
      ValueError: if the storage type is not supported.
    """
    if storage_type != definitions.STORAGE_TYPE_TASK:
      raise ValueError('Unsupported storage type: {0:s}.'.format(
          storage_type))
    super(RedisStore, self).__init__()
    if not session_identifier:
      session_identifier = str(uuid.uuid4())
    self._session_identifier = session_identifier
    if not task_identifier:
      task_identifier = str(uuid.uuid4())
    self._task_identifier = task_identifier
    self._redis_client = None
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON

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

  def _AddAttributeContainer(
      self, container_type, container, serialized_data=None):
    """Adds an attribute container to the store.

   Args:
      container_type (str): container type attribute of the container being
          added.
      container (AttributeContainer): unserialized attribute container.
      serialized_data (Optional[bytes]): serialized form of the container.
    """
    self._RaiseIfNotWritable()

    identifier = identifiers.RedisKeyIdentifier()
    container.SetIdentifier(identifier)

    if not serialized_data:
      serialized_data = self._SerializeAttributeContainer(container)

    container_key = self._GenerateRedisKey(container_type)
    string_identifier = identifier.CopyToString()
    self._redis_client.hset(container_key, string_identifier, serialized_data)

  def _GenerateRedisKey(self, key_suffix):
    """Generates a Redis key inside the appropriate namespace.

    Args:
      key_suffix (str): Redis key to be prefixed with the namespace value.

    Returns:
      str: a Redis key name.
    """
    return '{0:s}-{1:s}-{2:s}'.format(
        self._session_identifier, self._task_identifier, key_suffix)

  def _GetAttributeContainers(self, container_type):
    """Retrieves attribute containers

    Args:
      container_type (str): container type attribute of the container being
          added.

    Yields:
      AttributeContainer: attribute container.
    """
    container_key = self._GenerateRedisKey(container_type)
    for identifier, serialized_data in self._redis_client.hscan_iter(
        container_key):
      attribute_container = self._DeserializeAttributeContainer(
          container_type, serialized_data)

      identifier_string = identifier.decode('utf-8')
      redis_identifier = identifiers.RedisKeyIdentifier(identifier_string)
      attribute_container.SetIdentifier(redis_identifier)
      yield attribute_container

  def _GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves the container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (RedisKeyIdentifier): attributes container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    container_key = self._GenerateRedisKey(container_type)
    string_identifier = identifier.CopyToString()

    serialized_data = self._redis_client.hget(
        container_key, string_identifier)

    if not serialized_data:
      return None

    attribute_container = self._DeserializeAttributeContainer(
        container_type, serialized_data)

    attribute_container.SetIdentifier(identifier)
    return attribute_container

  def _GetNumberOfAttributeContainers(self, container_type):
    """Determines the number of containers of a type in the store.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers in the store of the specified type.
    """
    container_key = self._GenerateRedisKey(container_type)
    return self._redis_client.hlen(container_key)

  def _GetFinalizationKey(self):
    """Generates the finalized key for the store.

    Returns:
      str: Redis key for the the finalization flag.
    """
    return '{0:s}-{1:s}'.format(
        self._session_identifier, self._FINALIZED_KEY_NAME)

  def _HasAttributeContainers(self, container_type):
    """Determines if the store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    container_key = self._GenerateRedisKey(container_type)
    number_of_containers = self._redis_client.hlen(container_key)
    return  number_of_containers > 0

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

  def _WriteStorageMetadata(self):
    """Writes the storage metadata."""
    metadata = {
        'format_version': self._FORMAT_VERSION,
        'storage_type': definitions.STORAGE_TYPE_TASK,
        'serialization_format': self.serialization_format}
    metadata_key = self._GenerateRedisKey('metadata')

    for key, value in metadata.items():
      self._redis_client.hset(metadata_key, key, value)

  def _WriteAttributeContainer(self, attribute_container):
    """Writes an attribute container to the store.

    Args:
      attribute_container (AttributeContainer): attribute container.
    """
    container_type = attribute_container.CONTAINER_TYPE
    self._AddAttributeContainer(container_type, attribute_container)

  def AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): event.
      serialized_data (Optional[bytes]): serialized form of the event.
    """
    super(RedisStore, self).AddEvent(event, serialized_data=serialized_data)
    event_index_name = self._GenerateRedisKey(self._EVENT_INDEX_NAME)
    identifier = event.GetIdentifier()
    string_identifier = identifier.CopyToString()
    self._redis_client.zincrby(
        event_index_name, event.timestamp, string_identifier)

  def Close(self):
    """Closes the store."""
    self._redis_client = None

  def RemoveAttributeContainer(self, container_type, identifier):
    """Removes an attribute container from the store.

    Args:
      container_type (str): container type attribute of the container being
          removed.
      identifier (AttributeContainerIdentifier): event data identifier.
    """
    self._RaiseIfNotWritable()
    container_key = self._GenerateRedisKey(container_type)
    string_identifier = identifier.CopyToString()

    self._redis_client.hdel(container_key, string_identifier)
    if container_type == self._CONTAINER_TYPE_EVENT:
      event_index_name = self._GenerateRedisKey(self._EVENT_INDEX_NAME)
      self._redis_client.zrem(event_index_name, string_identifier)

  def RemoveAttributeContainers(self, container_type, container_identifiers):
    """Removes multiple attribute containers from the store.

    Args:
      container_type (str): container type attribute of the container being
          removed.
      container_identifiers (list[AttributeContainerIdentifier]):
          event data identifier.
    """
    self._RaiseIfNotWritable()
    if not container_identifiers:
      # If there's no list of identifiers, there's no need to delete anything.
      return
    container_key = self._GenerateRedisKey(container_type)
    string_identifiers = [
        identifier.CopyToString() for identifier in container_identifiers]

    self._redis_client.hdel(container_key, *string_identifiers)
    if container_type == self._CONTAINER_TYPE_EVENT:
      event_index_name = self._GenerateRedisKey(self._EVENT_INDEX_NAME)
      self._redis_client.zrem(event_index_name, *string_identifiers)

  def IsFinalized(self):
    """Checks if a store has been finalized.

    Returns:
      bool: True if the store has been finalized.
    """
    self._RaiseIfNotReadable()

    finalized_key = self._GetFinalizationKey()
    finalized_value = self._redis_client.hget(
        finalized_key, self._task_identifier)

    return finalized_value == self._FINALIZED_BYTES

  def Finalize(self):
    """Marks a store as finalized.

    No further attribute containers will be written to a finalized store.
    """
    self._RaiseIfNotWritable()

    finalized_key = self._GetFinalizationKey()
    self._redis_client.hset(
        finalized_key, self._task_identifier, self._FINALIZED_BYTES)

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
    event_index_name = self._GenerateRedisKey(self._EVENT_INDEX_NAME)
    if time_range:
      raise RuntimeError('Not supported')

    sorted_event_identifiers = self._redis_client.zscan_iter(event_index_name)
    for event_identifier, _ in sorted_event_identifiers:
      identifier_string = event_identifier.decode('utf-8')
      event_identifier = identifiers.RedisKeyIdentifier(identifier_string)
      yield self._GetAttributeContainerByIdentifier(
          self._CONTAINER_TYPE_EVENT, event_identifier)

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
    name = self._GenerateRedisKey(container_type)
    # Redis treats None as meaning "no limit", not 0.
    if maximum_number_of_items == 0:
      maximum_number_of_items = None

    cursor, items = self._redis_client.hscan(
        name, cursor=cursor, count=maximum_number_of_items)
    return cursor, items

  # pylint: disable=arguments-differ
  def Open(self, redis_client=None, url=None, **unused_kwargs):
    """Opens the store.

    Args:
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created. If no client is specified a new client
          will be opened connected to the Redis instance specified by 'url'.
      url (Optional[str]): URL for a Redis database. If not specified, the
          DEFAULT_REDIS_URL will be used.

    Raises:
      IOError: if the store is already connected to a Redis instance.
      OSError: if the store is already connected to a Redis instance.
    """
    if not url:
      url = self.DEFAULT_REDIS_URL

    if self._redis_client:
      raise IOError('Redis client already connected')

    if redis_client:
      self._redis_client = redis_client
    else:
      self._redis_client = redis.from_url(url=url, socket_timeout=60)

    client_name = self._GenerateRedisKey('')
    self._SetClientName(self._redis_client, client_name)

    metadata_key = self._GenerateRedisKey('metadata')
    if not self._redis_client.exists(metadata_key):
      self._WriteStorageMetadata()

  def Remove(self):
    """Removes the contents of the store from Redis."""
    merging_key = '{0:s}-{1:s}'.format(
        self._session_identifier, self._MERGING_KEY_NAME)
    self._redis_client.hdel(merging_key, self._task_identifier)

    sorted_event_key = self._GenerateRedisKey(self._EVENT_INDEX_NAME)
    self._redis_client.delete(sorted_event_key)

    task_completion_key = self._GenerateRedisKey(
        self._CONTAINER_TYPE_TASK_COMPLETION)
    self._redis_client.delete(task_completion_key)

    metadata_key = self._GenerateRedisKey('metadata')
    self._redis_client.delete(metadata_key)

  @classmethod
  def ScanForProcessedTasks(
      cls, session_identifier, redis_client=None, url=None):
    """Scans a Redis database for processed tasks.

    Args:
      session_identifier (str): session identifier, formatted as
          a UUID.
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created.
      url (Optional[str]): URL for a Redis database. If not specified,
          REDIS_DEFAULT_URL will be used.

    Returns:
      tuple: containing
          list[str]: identifiers of processed tasks, which may be empty if the
              connection to Redis times out.
          Redis: Redis client used for the query.
    """
    if not url:
      url = cls.DEFAULT_REDIS_URL

    if not redis_client:
      redis_client = redis.from_url(url=url, socket_timeout=60)
      cls._SetClientName(redis_client, 'processed_scan')

    finalization_key = '{0:s}-{1:s}'.format(
        session_identifier, cls._FINALIZED_KEY_NAME)
    try:
      task_identifiers = redis_client.hkeys(finalization_key)
    except redis.exceptions.TimeoutError:
      # If there is a timeout fetching identifiers, we assume that there are
      # no processed tasks.
      return [], redis_client
    task_identifiers = [key.decode('utf-8') for key in task_identifiers]
    return task_identifiers, redis_client

  @classmethod
  def MarkTaskAsMerging(
      cls, task_identifier, session_identifier, redis_client=None, url=None):
    """Marks a finalized task as pending merge.

    Args:
      task_identifier (str): identifier of the task.
      session_identifier (str): session identifier, formatted as a UUID.
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created.
      url (Optional[str]): URL for a Redis database. If not specified,
          REDIS_DEFAULT_URL will be used.

    Raises:
      IOError: if the task being updated is not finalized.
      OSError: if the task being updated is not finalized.
    """
    if not url:
      url = cls.DEFAULT_REDIS_URL

    if not redis_client:
      redis_client = redis.from_url(url=url, socket_timeout=60)

    cls._SetClientName(redis_client, 'merge_mark')

    finalization_key = '{0:s}-{1:s}'.format(
        session_identifier, cls._FINALIZED_KEY_NAME)
    number_of_deleted_fields = redis_client.hdel(
        finalization_key, task_identifier)
    if number_of_deleted_fields == 0:
      raise IOError('Task identifier {0:s} not finalized'.format(
          task_identifier))

    merging_key = '{0:s}-{1:s}'.format(
        session_identifier, cls._MERGING_KEY_NAME)
    redis_client.hset(merging_key, task_identifier, cls._MERGING_BYTES)
