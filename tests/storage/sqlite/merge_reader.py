#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the merge reader for SQLite storage files."""

from __future__ import unicode_literals

import os
import unittest

from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage.sqlite import merge_reader
from plaso.storage.sqlite import writer

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class SQLiteStorageMergeReaderTest(test_lib.StorageTestCase):
  """Tests for the SQLite-based storage file reader for merging."""

  # pylint: disable=protected-access

  _TEST_EVENTS_WITH_DESERIALIZATION_ERROR = [
      {'data_type': 'windows:registry:key_value',
       'key_path': 'MY AutoRun key',
       'parser': 'UNKNOWN',
       'timestamp': '2012-04-20 22:38:46.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: c:/Temp/evil.exe'}]

  def _CreateTaskStorageFile(self, session, path, event_values_list):
    """Creates a task storage file for testing.

    Args:
      session (Session): session the task storage is part of.
      path (str): path to the task storage file that should be merged.
      event_values_list (list[dict[str, str]]): list of event values.
    """
    task = tasks.Task(session_identifier=session.identifier)

    storage_file = writer.SQLiteStorageFileWriter(
        session, path, storage_type=definitions.STORAGE_TYPE_TASK, task=task)

    storage_file.Open()

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(event_values_list)):
      storage_file.AddEventDataStream(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_file.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_file.AddEvent(event)

    storage_file.Close()

  def testReadStorageMetadata(self):
    """Tests the _ReadStorageMetadata function."""
    session = sessions.Session()

    with shared_test_lib.TempDirectory() as temp_directory:
      task_storage_path = os.path.join(temp_directory, 'task.sqlite')
      self._CreateTaskStorageFile(session, task_storage_path, self._TEST_EVENTS)

      session_storage_path = os.path.join(temp_directory, 'plaso.sqlite')
      storage_writer = writer.SQLiteStorageFileWriter(
          session, session_storage_path)

      test_reader = merge_reader.SQLiteStorageMergeReader(
          storage_writer, task_storage_path)

      test_reader._Open()
      test_reader._ReadStorageMetadata()
      test_reader._Close()

  def testMergeAttributeContainers(self):
    """Tests the MergeAttributeContainers function."""
    session = sessions.Session()

    with shared_test_lib.TempDirectory() as temp_directory:
      task_storage_path = os.path.join(temp_directory, 'task.sqlite')
      self._CreateTaskStorageFile(session, task_storage_path, self._TEST_EVENTS)

      session_storage_path = os.path.join(temp_directory, 'plaso.sqlite')
      storage_writer = writer.SQLiteStorageFileWriter(
          session, session_storage_path)

      test_reader = merge_reader.SQLiteStorageMergeReader(
          storage_writer, task_storage_path)

      storage_writer.Open()

      result = test_reader.MergeAttributeContainers()
      self.assertTrue(result)

      storage_writer.Close()

  def testMergeAttributeContainersWithDeserializationError(self):
    """Tests MergeAttributeContainers with a deserialization error."""
    session = sessions.Session()

    with shared_test_lib.TempDirectory() as temp_directory:
      task_storage_path = os.path.join(temp_directory, 'task.sqlite')
      self._CreateTaskStorageFile(
          session, task_storage_path,
          self._TEST_EVENTS_WITH_DESERIALIZATION_ERROR)

      session_storage_path = os.path.join(temp_directory, 'plaso.sqlite')
      storage_writer = writer.SQLiteStorageFileWriter(
          session, session_storage_path)

      test_reader = merge_reader.SQLiteStorageMergeReader(
          storage_writer, task_storage_path)

      storage_writer.Open()

      result = test_reader.MergeAttributeContainers()
      self.assertTrue(result)

      storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
