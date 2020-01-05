#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the merge reader for redis stores."""
from __future__ import unicode_literals

import os

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
  """Tests for the redis store reader for merging."""

  def _CreateTaskStore(self, session):
    """Creates a task storage file for testing.

    Args:
      session (Session): session the task store is part of.

    Returns:
      Task: the the task for the store that was created.
    """
    task = tasks.Task(session_identifier=session.identifier)

    task_store = redis_writer.RedisStorageWriter(
        session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)

    task_store.Open()

    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      task_store.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      task_store.AddEvent(event)

    task_store.Close()

    return task

  def testMergeAttributeContainers(self):
    """Tests the MergeAttributeContainers function."""
    session = sessions.Session()

    with shared_test_lib.TempDirectory() as temp_directory:
      task = self._CreateTaskStore(session)

      session_storage_path = os.path.join(temp_directory, 'plaso.sqlite')
      storage_writer = writer.SQLiteStorageFileWriter(
          session, session_storage_path)

      test_reader = merge_reader.RedisMergeReader(storage_writer, task)

      ready_tasks, _ = redis_store.RedisStore.ScanForProcessedTasks(
          session_identifier=session.identifier)
      self.assertEqual(1, len(ready_tasks))

      storage_writer.Open()

      result = test_reader.MergeAttributeContainers()
      self.assertTrue(result)

      storage_writer.Close()
