#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Redis storage."""

import unittest

try:
  # pylint: disable=ungrouped-imports
  import fakeredis
  import redis
  from plaso.storage.redis import redis_store
except ModuleNotFoundError:
  redis = None

from plaso.containers import events
from plaso.containers import sessions
from plaso.containers import tasks

from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


@unittest.skipIf(redis is None, 'missing redis support')
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

  def _RemoveSessionData(self, redis_client, session_identifier):
    """Removes the session data after testing.

    Args:
      redis_client (Redis): an open Redis client.
      session_identifier (str): the identifier of the session the tasks are
          part of.
    """
    redis_hash_pattern = '{0:s}-*'.format(session_identifier)

    for redis_hash_name in redis_client.keys(redis_hash_pattern):
      redis_client.delete(redis_hash_name)

  def testGetRedisHashName(self):
    """Tests the _GetRedisHashName function."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    event_data_stream = events.EventDataStream()

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      redis_hash_name = test_store._GetRedisHashName(
          event_data_stream.CONTAINER_TYPE)

      expected_redis_hash_name = '{0:s}-{1:s}-{2:s}'.format(
          task.session_identifier, task.identifier,
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(redis_hash_name, expected_redis_hash_name)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  # TODO: add tests for _GetFinalizationKey
  # TODO: add tests for _RaiseIfNotReadable
  # TODO: add tests for _RaiseIfNotWritable
  # TODO: add tests for _SetClientName

  def testWriteExistingAttributeContainer(self):
    """Tests the _WriteExistingAttributeContainer function."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=session.identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store._WriteNewAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store._WriteExistingAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testWriteNewAttributeContainer(self):
    """Tests the _WriteNewAttributeContainer method."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store._WriteNewAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer method."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store.AddAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

    with self.assertRaises(IOError):
      test_store.AddAttributeContainer(event_data_stream)

  # TODO: add tests for _WriteStorageMetadata

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier method."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      test_store.AddAttributeContainer(event_data_stream)
      identifier = event_data_stream.GetIdentifier()

      container = test_store.GetAttributeContainerByIdentifier(
          event_data_stream.CONTAINER_TYPE, identifier)
      self.assertIsNotNone(container)

      identifier.sequence_number = 99

      container = test_store.GetAttributeContainerByIdentifier(
          event_data_stream.CONTAINER_TYPE, identifier)
      self.assertIsNone(container)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testGetAttributeContainerByIndex(self):
    """Tests the GetAttributeContainerByIndex function."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      container = test_store.GetAttributeContainerByIndex(
          event_data_stream.CONTAINER_TYPE, 0)
      self.assertIsNone(container)

      test_store.AddAttributeContainer(event_data_stream)

      container = test_store.GetAttributeContainerByIndex(
          event_data_stream.CONTAINER_TYPE, 0)
      self.assertIsNotNone(container)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testGetAttributeContainers(self):
    """Tests the GetAttributeContainers method."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()
      event_data_stream.md5_hash = '8f0bf95a7959baad9666b21a7feed79d'

      containers = list(test_store.GetAttributeContainers(
          event_data_stream.CONTAINER_TYPE))
      self.assertEqual(len(containers), 0)

      test_store.AddAttributeContainer(event_data_stream)

      containers = list(test_store.GetAttributeContainers(
          event_data_stream.CONTAINER_TYPE))
      self.assertEqual(len(containers), 1)

      filter_expression = 'md5_hash == "8f0bf95a7959baad9666b21a7feed79d"'
      containers = list(test_store.GetAttributeContainers(
          event_data_stream.CONTAINER_TYPE,
          filter_expression=filter_expression))
      self.assertEqual(len(containers), 1)

      filter_expression = 'md5_hash != "8f0bf95a7959baad9666b21a7feed79d"'
      containers = list(test_store.GetAttributeContainers(
          event_data_stream.CONTAINER_TYPE,
         filter_expression=filter_expression))
      self.assertEqual(len(containers), 0)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testGetNumberOfAttributeContainers(self):
    """Tests the GetNumberOfAttributeContainers function."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store.AddAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testGetSerializedAttributeContainers(self):
    """Tests the GetSerializedAttributeContainers method."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      for _, event_data, _ in containers_test_lib.CreateEventsFromValues(
          self._TEST_EVENTS):
        test_store.AddAttributeContainer(event_data)

      cursor, serialized_containers = (
          test_store.GetSerializedAttributeContainers('event_data', 0, 0))
      self.assertEqual(len(serialized_containers), 4)
      for serialized_container in serialized_containers:
        self.assertIsInstance(serialized_container, bytes)
      self.assertIsInstance(cursor, int)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents method."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      for event, _, _ in containers_test_lib.CreateEventsFromValues(
          self._TEST_EVENTS):
        test_store.AddAttributeContainer(event)

      retrieved_events = list(test_store.GetSortedEvents())
      self.assertEqual(len(retrieved_events), 4)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  def testHasAttributeContainers(self):
    """Tests the HasAttributeContainers method."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      result = test_store.HasAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertFalse(result)

      test_store.AddAttributeContainer(event_data_stream)

      result = test_store.HasAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertTrue(result)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)

  # TODO: add tests for Open and Close

  def testUpdateAttributeContainer(self):
    """Tests the UpdateAttributeContainer function."""
    redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_store = redis_store.RedisStore()
    test_store.Open(
        redis_client=redis_client, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      event_data_stream = events.EventDataStream()

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      test_store.AddAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      test_store.UpdateAttributeContainer(event_data_stream)

      number_of_containers = test_store.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

    finally:
      test_store.Close()

      self._RemoveSessionData(redis_client, session.identifier)


if __name__ == '__main__':
  unittest.main()
