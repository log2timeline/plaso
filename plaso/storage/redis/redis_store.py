# -*- coding: utf-8 -*-
"""Redis store.

Only supports task storage at the moment.
"""

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

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a Redis store.

    Args:
      storage_type (Optional[str]): storage type.

    Raises:
      ValueError: if the storage type is not supported.
    """
    if storage_type != definitions.STORAGE_TYPE_TASK:
      raise ValueError('Unsupported storage type: {0:s}.'.format(
          storage_type))

    super(RedisStore, self).__init__(storage_type=storage_type)
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

  # pylint: disable=redundant-returns-doc
  def GetEventTagByEventIdentifier(self, event_identifier):
    """Retrieves the event tag related to a specific event identifier.

    Args:
      event_identifier (AttributeContainerIdentifier): event.

    Returns:
      EventTag: event tag or None if not available.
    """
    # Note that the Redis store is only used for storing tasks and does not
    # support this method. None is returned to have code using this method
    # add an event tag instead of updating the existing one.
    return None

  def _GetFinalizationKey(self):
    """Generates the finalized key for the store.

    Returns:
      str: Redis key for the the finalization flag.
    """
    return '{0:s}-{1:s}'.format(
        self._session_identifier, self._FINALIZED_KEY_NAME)

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

    serialized_data = self._SerializeAttributeContainer(container)
    self._redis_client.hset(redis_hash_name, redis_key, serialized_data)

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

    serialized_data = self._SerializeAttributeContainer(container)
    self._redis_client.hsetnx(redis_hash_name, redis_key, serialized_data)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      index_name = self._GetRedisHashName(self._EVENT_INDEX_NAME)
      self._redis_client.zincrby(index_name, container.timestamp, redis_key)

  def _WriteStorageMetadata(self):
    """Writes the storage metadata."""
    metadata = {
        'format_version': self._FORMAT_VERSION,
        'storage_type': definitions.STORAGE_TYPE_TASK,
        'serialization_format': self.serialization_format}
    metadata_key = self._GetRedisHashName('metadata')

    for key, value in metadata.items():
      self._redis_client.hset(metadata_key, key, value)

  def Close(self):
    """Closes the store.

    Raises:
      IOError: if the store is already closed.
      OSError: if the store is already closed.
    """
    if not self._redis_client:
      raise IOError('Store already closed.')

    finalized_key = self._GetFinalizationKey()
    self._redis_client.hset(
        finalized_key, self._task_identifier, self._FINALIZED_BYTES)

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
    return attribute_container

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: if the attribute container type is not supported.
      OSError: if the attribute container type is not supported.
    """
    if container_type not in self._CONTAINER_TYPES:
      raise IOError('Unsupported attribute container type: {0:s}'.format(
          container_type))

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
    return attribute_container

  def GetAttributeContainers(self, container_type):
    """Retrieves attribute containers

    Args:
      container_type (str): container type attribute of the container being
          added.

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

  # pylint: disable=arguments-differ
  def Open(
      self, redis_client=None, session_identifier=None, task_identifier=None,
      url=None, **unused_kwargs):
    """Opens the store.

    Args:
      redis_client (Optional[Redis]): Redis client to query. If specified, no
          new client will be created. If no client is specified a new client
          will be opened connected to the Redis instance specified by 'url'.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
      task_identifier (Optional[str]): unique identifier of the task the store
          will store containers for. If not specified, an identifier will be
          generated.
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

    self._session_identifier = session_identifier or str(uuid.uuid4())
    self._task_identifier = task_identifier or str(uuid.uuid4())

    client_name = self._GetRedisHashName('')
    self._SetClientName(self._redis_client, client_name)

    metadata_key = self._GetRedisHashName('metadata')
    if not self._redis_client.exists(metadata_key):
      self._WriteStorageMetadata()

  def Remove(self):
    """Removes the contents of the store from Redis."""
    merging_key = '{0:s}-{1:s}'.format(
        self._session_identifier, self._MERGING_KEY_NAME)
    self._redis_client.hdel(merging_key, self._task_identifier)

    sorted_event_key = self._GetRedisHashName(self._EVENT_INDEX_NAME)
    self._redis_client.delete(sorted_event_key)

    task_completion_key = self._GetRedisHashName(
        self._CONTAINER_TYPE_TASK_COMPLETION)
    self._redis_client.delete(task_completion_key)

    metadata_key = self._GetRedisHashName('metadata')
    self._redis_client.delete(metadata_key)

  def RemoveAttributeContainer(self, container_type, identifier):
    """Removes an attribute container from the store.

    Args:
      container_type (str): container type attribute of the container being
          removed.
      identifier (AttributeContainerIdentifier): event data identifier.
    """
    self._RaiseIfNotWritable()
    redis_hash_name = self._GetRedisHashName(container_type)
    redis_key = identifier.CopyToString()

    self._redis_client.hdel(redis_hash_name, redis_key)
    if container_type == self._CONTAINER_TYPE_EVENT:
      event_index_name = self._GetRedisHashName(self._EVENT_INDEX_NAME)
      self._redis_client.zrem(event_index_name, redis_key)

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

    redis_hash_name = self._GetRedisHashName(container_type)
    redis_keys = [
        identifier.CopyToString() for identifier in container_identifiers]

    self._redis_client.hdel(redis_hash_name, *redis_keys)

    if container_type == self._CONTAINER_TYPE_EVENT:
      event_index_name = self._GetRedisHashName(self._EVENT_INDEX_NAME)
      self._redis_client.zrem(event_index_name, *redis_keys)

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
