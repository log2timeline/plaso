#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the merge reader for Redis stores."""

import os
import unittest

import fakeredis
import redis

from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage.redis import merge_reader
from plaso.storage.redis import redis_store
from plaso.storage.redis import writer as redis_writer
from plaso.storage.sqlite import writer

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class RedisMergeReaderTest(test_lib.StorageTestCase):
  """Tests for the Redis store reader for merging."""

  _REDIS_URL = 'redis://127.0.0.1/0'

  def _GetRedisClient(self):
    """Creates a Redis client for testing.

    This method will attempt to use a Redis server listening on localhost and
    fallback to a fake Redis client if no server is availble or the connection
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

  def _CreateTaskStore(self, session, redis_client):
    """Creates a task store for testing.

    Args:
      session (Session): session the task store is part of.
      redis_client (Redis): Redis client to query. If specified, no
          new client will be created.

    Returns:
      Task: the the task for the store that was created.
    """
    task = tasks.Task(session_identifier=session.identifier)

    task_store = redis_writer.RedisStorageWriter(
        session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)

    task_store.Open(redis_client=redis_client)

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      task_store.AddEventDataStream(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      task_store.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      task_store.AddEvent(event)

    task_store.Close()

    return task

  def testMergeAttributeContainers(self):
    """Tests the MergeAttributeContainers function."""
    session = sessions.Session()
    client = self._GetRedisClient()

    with shared_test_lib.TempDirectory() as temp_directory:
      task = self._CreateTaskStore(session, redis_client=client)

      session_storage_path = os.path.join(temp_directory, 'plaso.sqlite')
      storage_writer = writer.SQLiteStorageFileWriter(
          session, session_storage_path)

      test_reader = merge_reader.RedisMergeReader(
          storage_writer, task, redis_client=client)

      ready_tasks, _ = redis_store.RedisStore.ScanForProcessedTasks(
          session_identifier=session.identifier, redis_client=client)
      self.assertEqual(1, len(ready_tasks))

      storage_writer.Open()

      result = test_reader.MergeAttributeContainers()
      self.assertTrue(result)

      storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
