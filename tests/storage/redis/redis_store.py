#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Redis storage."""

import unittest

import fakeredis
import redis

from plaso.containers import events
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.storage.redis import redis_store
from plaso.storage.redis import writer

from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class RedisStoreTest(test_lib.StorageTestCase):
  """Tests for the Redis storage object."""

  # pylint: disable=protected-access

  _REDIS_URL = 'redis://127.0.0.1/0'

  def _GetRedisClient(self):
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

  # TODO: add tests for _Finalize

  # TODO: add tests for _GenerateRedisKey

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier method."""
    test_events = []
    for test_event, _, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_events.append(test_event)

    test_event_tags = self._CreateTestEventTags(test_events)
    test_event_tag = test_event_tags[0]

    test_store = redis_store.RedisStore()
    redis_client = self._GetRedisClient()
    test_store.Open(redis_client=redis_client)

    test_store.AddAttributeContainer(test_event_tag)

    identifier = test_event_tag.GetIdentifier()

    retrieved_event_tag = test_store.GetAttributeContainerByIdentifier(
        test_event_tag.CONTAINER_TYPE, identifier)

    test_event_tag_dict = test_event_tag.CopyToDict()
    retrieved_event_tag_dict = retrieved_event_tag.CopyToDict()

    self.assertEqual(test_event_tag_dict, retrieved_event_tag_dict)

    test_store.Close()

  # TODO: add tests for _GetFinalizationKey
  # TODO: add tests for _RaiseIfNotReadable
  # TODO: add tests for _RaiseIfNotWritable
  # TODO: add tests for _SetClientName

  def testWriteNewAttributeContainers(self):
    """Tests the _WriteNewAttributeContainer method."""
    event_data = events.EventData()

    test_store = redis_store.RedisStore()
    redis_client = self._GetRedisClient()
    test_store.Open(redis_client=redis_client)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store._WriteNewAttributeContainer(event_data)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    has_containers = test_store.HasAttributeContainers(
        event_data.CONTAINER_TYPE)
    self.assertTrue(has_containers)

    test_store.Close()

  # TODO: add tests for _WriteStorageMetadata

  def testGetAttributeContainers(self):
    """Tests the GetAttributeContainers method."""
    test_store = redis_store.RedisStore()
    redis_client = self._GetRedisClient()
    test_store.Open(redis_client=redis_client)

    for _, event_data, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_store.AddAttributeContainer(event_data)

    containers = list(test_store.GetAttributeContainers(
        test_store._CONTAINER_TYPE_EVENT_DATA))
    self.assertEqual(len(containers), 4)

    test_store.Close()

  # TODO: add tests for GetNumberOfAttributeContainers

  def testGetSerializedAttributeContainers(self):
    """Tests the GetSerializedAttributeContainers method."""
    test_store = redis_store.RedisStore()
    redis_client = self._GetRedisClient()
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
    test_store = redis_store.RedisStore()
    redis_client = self._GetRedisClient()
    test_store.Open(redis_client=redis_client)

    for event, _, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_store.AddAttributeContainer(event)

    retrieved_events = list(test_store.GetSortedEvents())
    self.assertEqual(len(retrieved_events), 4)

    test_store.Close()

  # TODO: add tests for HasAttributeContainers

  # TODO: add tests for Open and Close

  def testMarkTaskAsMerging(self):
    """Tests the MarkTaskAsMerging method"""
    redis_client = self._GetRedisClient()
    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    # Trying to mark a task as merging without finalizing it raises an error.
    with self.assertRaises(IOError):
      redis_store.RedisStore.MarkTaskAsMerging(
          task.identifier, session.identifier, redis_client=redis_client)

    # Opening and closing a writer for a task should cause the task to be marked
    # as complete.
    storage_writer = writer.RedisStorageWriter(session, task=task)
    storage_writer.Open(redis_client=redis_client)
    storage_writer.Close()

    redis_store.RedisStore.MarkTaskAsMerging(
        task.identifier, session.identifier, redis_client=redis_client)

  # TODO: add tests for Remove

  def testRemoveAttributeContainer(self):
    """Tests the RemoveAttributeContainer method."""
    event_data = events.EventData()

    test_store = redis_store.RedisStore()
    redis_client = self._GetRedisClient()
    test_store.Open(redis_client=redis_client)

    test_store.AddAttributeContainer(event_data)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    identifier = event_data.GetIdentifier()
    test_store.RemoveAttributeContainer(
        test_store._CONTAINER_TYPE_EVENT_DATA, identifier)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store.Close()

  # TODO: add tests for RemoveAttributeContainers

  def testScanForProcessedTasks(self):
    """Tests the ScanForProcessedTasks method"""
    redis_client = self._GetRedisClient()
    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    # There should be no processed task identifiers initially.
    task_identifiers, _ = redis_store.RedisStore.ScanForProcessedTasks(
        session.identifier, redis_client=redis_client)
    self.assertEqual([], task_identifiers)

    # Opening and closing a writer for a task should cause the task to be marked
    # as complete.
    storage_writer = writer.RedisStorageWriter(session, task=task)
    storage_writer.Open(redis_client=redis_client)
    storage_writer.Close()

    # The task store is now marked as processed.
    task_identifiers, _ = redis_store.RedisStore.ScanForProcessedTasks(
        session.identifier, redis_client=redis_client)
    self.assertEqual([task.identifier], task_identifiers)


if __name__ == '__main__':
  unittest.main()
