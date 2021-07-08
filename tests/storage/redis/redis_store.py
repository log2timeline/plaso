#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Redis storage."""

import unittest

import fakeredis
import redis

from plaso.containers import events
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage.redis import redis_store
from plaso.storage.redis import writer

from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class RedisStoreTest(test_lib.StorageTestCase):
  """Tests for the Redis storage object."""

  # pylint: disable=protected-access

  _REDIS_URL = 'redis://127.0.0.1/0'

  def _CreateRedisClient(self):
    """Creates a Redis client for testing.

    This method will attempt to use a Redis server listening on localhost and
    fallback to a fake Redis client if no server is available or the connection
    timed out.

    Returns:
      Redis: a Redis client.
    """
    try:
      redis_client = redis.from_url(self._REDIS_URL, socket_timeout=60)
      redis_client.ping()
    except redis.exceptions.ConnectionError:
      redis_client = fakeredis.FakeStrictRedis()

    return redis_client

  def testGetRedisHashName(self):
    """Tests the _GetRedisHashName function."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    redis_hash_name = test_store._GetRedisHashName(
        event_data_stream.CONTAINER_TYPE)

    expected_redis_hash_name = '{0:s}-{1:s}-{2:s}'.format(
        task.session_identifier, task.identifier,
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(redis_hash_name, expected_redis_hash_name)

  # TODO: add tests for _GetFinalizationKey
  # TODO: add tests for _RaiseIfNotReadable
  # TODO: add tests for _RaiseIfNotWritable
  # TODO: add tests for _SetClientName

  def testWriteExistingAttributeContainer(self):
    """Tests the _WriteExistingAttributeContainer function."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    with self.assertRaises(IOError):
      test_store._WriteExistingAttributeContainer(event_data_stream)

    test_store._WriteNewAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store._WriteExistingAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

  def testWriteNewAttributeContainer(self):
    """Tests the _WriteNewAttributeContainer method."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store._WriteNewAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer method."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store.AddAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

    with self.assertRaises(IOError):
      test_store.AddAttributeContainer(event_data_stream)

  # TODO: add tests for _WriteStorageMetadata

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier method."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    test_store.AddAttributeContainer(event_data_stream)
    identifier = event_data_stream.GetIdentifier()

    container = test_store.GetAttributeContainerByIdentifier(
        event_data_stream.CONTAINER_TYPE, identifier)
    self.assertIsNotNone(container)

    identifier.sequence_number = 99

    container = test_store.GetAttributeContainerByIdentifier(
        event_data_stream.CONTAINER_TYPE, identifier)
    self.assertIsNone(container)

    test_store.Close()

  def testGetAttributeContainerByIndex(self):
    """Tests the GetAttributeContainerByIndex function."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    container = test_store.GetAttributeContainerByIndex(
        event_data_stream.CONTAINER_TYPE, 0)
    self.assertIsNone(container)

    test_store.AddAttributeContainer(event_data_stream)

    container = test_store.GetAttributeContainerByIndex(
        event_data_stream.CONTAINER_TYPE, 0)
    self.assertIsNotNone(container)

    with self.assertRaises(IOError):
      test_store.GetAttributeContainerByIndex('bogus', 0)

    test_store.Close()

  def testGetAttributeContainers(self):
    """Tests the GetAttributeContainers method."""
    redis_client = self._CreateRedisClient()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    for _, event_data, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_store.AddAttributeContainer(event_data)

    containers = list(test_store.GetAttributeContainers(
        test_store._CONTAINER_TYPE_EVENT_DATA))
    self.assertEqual(len(containers), 4)

    test_store.Close()

  def testGetEventTagByEventIdentifier(self):
    """Tests the GetEventTagByEventIdentifier function."""
    redis_client = self._CreateRedisClient()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    index = 0
    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      test_store.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(
          event_data_stream.GetIdentifier())
      test_store.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      test_store.AddAttributeContainer(event)

      if index == 1:
        event_tag = events.EventTag()
        event_tag.AddLabels(['Malware', 'Benign'])

        event_identifier = event.GetIdentifier()
        event_tag.SetEventIdentifier(event_identifier)
        test_store.AddAttributeContainer(event_tag)

      index += 1

    test_store.Close()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    test_event = test_store.GetAttributeContainerByIndex(
        events.EventObject.CONTAINER_TYPE, 1)
    # Note that this method is not implemented.
    self.assertIsNone(test_event)

    test_store.Close()

  def testGetNumberOfAttributeContainers(self):
    """Tests the GetNumberOfAttributeContainers function."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store.AddAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

  def testGetSerializedAttributeContainers(self):
    """Tests the GetSerializedAttributeContainers method."""
    redis_client = self._CreateRedisClient()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    for _, event_data, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_store.AddAttributeContainer(event_data)

    cursor, serialized_containers = test_store.GetSerializedAttributeContainers(
        'event_data', 0, 0)
    self.assertEqual(len(serialized_containers), 4)
    for serialized_container in serialized_containers:
      self.assertIsInstance(serialized_container, bytes)
    self.assertIsInstance(cursor, int)

    test_store.Close()

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents method."""
    redis_client = self._CreateRedisClient()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    for event, _, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_store.AddAttributeContainer(event)

    retrieved_events = list(test_store.GetSortedEvents())
    self.assertEqual(len(retrieved_events), 4)

    test_store.Close()

  def testHasAttributeContainers(self):
    """Tests the HasAttributeContainers method."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    result = test_store.HasAttributeContainers(event_data_stream.CONTAINER_TYPE)
    self.assertFalse(result)

    test_store.AddAttributeContainer(event_data_stream)

    result = test_store.HasAttributeContainers(event_data_stream.CONTAINER_TYPE)
    self.assertTrue(result)

    test_store.Close()

  # TODO: add tests for Open and Close

  def testMarkTaskAsMerging(self):
    """Tests the MarkTaskAsMerging method"""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    # Trying to mark a task as merging without finalizing it raises an error.
    with self.assertRaises(IOError):
      redis_store.RedisStore.MarkTaskAsMerging(
          task.identifier, session.identifier, redis_client=redis_client)

    # Opening and closing a writer for a task should cause the task to be marked
    # as complete.
    storage_writer = writer.RedisStorageWriter(
        storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)
    storage_writer.Close()

    redis_store.RedisStore.MarkTaskAsMerging(
        task.identifier, session.identifier, redis_client=redis_client)

  # TODO: add tests for Remove

  def testRemoveAttributeContainer(self):
    """Tests the RemoveAttributeContainer method."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    test_store.AddAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    identifier = event_data_stream.GetIdentifier()
    test_store.RemoveAttributeContainer(
        event_data_stream.CONTAINER_TYPE, identifier)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store.Close()

  # TODO: add tests for RemoveAttributeContainers

  def testScanForProcessedTasks(self):
    """Tests the ScanForProcessedTasks method"""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    # There should be no processed task identifiers initially.
    task_identifiers, _ = redis_store.RedisStore.ScanForProcessedTasks(
        session.identifier, redis_client=redis_client)
    self.assertEqual([], task_identifiers)

    # Opening and closing a writer for a task should cause the task to be marked
    # as complete.
    storage_writer = writer.RedisStorageWriter(
        storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)
    storage_writer.Close()

    # The task store is now marked as processed.
    task_identifiers, _ = redis_store.RedisStore.ScanForProcessedTasks(
        session.identifier, redis_client=redis_client)
    self.assertEqual([task.identifier], task_identifiers)

  def testUpdateAttributeContainer(self):
    """Tests the UpdateAttributeContainer function."""
    redis_client = self._CreateRedisClient()

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open(redis_client=redis_client)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    with self.assertRaises(IOError):
      test_store.UpdateAttributeContainer(event_data_stream)

    test_store.AddAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.UpdateAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()


if __name__ == '__main__':
  unittest.main()
