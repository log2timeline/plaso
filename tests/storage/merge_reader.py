#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the merge reader."""

import os
import unittest

from plaso.containers import sessions
from plaso.lib import definitions
from plaso.storage import merge_reader
from plaso.storage.sqlite import reader as sqlite_reader
from plaso.storage.sqlite import writer as sqlite_writer

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class StorageMergeReaderTest(test_lib.StorageTestCase):
  """Tests for the merge reader."""

  # pylint: disable=protected-access

  _TEST_EVENTS_WITH_DESERIALIZATION_ERROR = [
      {'data_type': 'windows:registry:key_value',
       'key_path': 'MY AutoRun key',
       'parser': 'UNKNOWN',
       'timestamp': '2012-04-20 22:38:46.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: c:/Temp/evil.exe'}]

  def _CreateTaskStorageFile(self, path, event_values_list):
    """Creates a task storage file for testing.

    Args:
      path (str): path to the task storage file that should be merged.
      event_values_list (list[dict[str, str]]): list of event values.
    """
    storage_writer = sqlite_writer.SQLiteStorageFileWriter(
        storage_type=definitions.STORAGE_TYPE_TASK)

    storage_writer.Open(path=path)

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(event_values_list)):
      storage_writer.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_writer.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddAttributeContainer(event)

    storage_writer.Close()

  def testMergeAttributeContainers(self):
    """Tests the MergeAttributeContainers function."""
    session = sessions.Session()

    with shared_test_lib.TempDirectory() as temp_directory:
      task_storage_path = os.path.join(temp_directory, 'task.sqlite')
      self._CreateTaskStorageFile(task_storage_path, self._TEST_EVENTS)

      session_storage_path = os.path.join(temp_directory, 'plaso.sqlite')
      storage_writer = sqlite_writer.SQLiteStorageFileWriter(
          session_storage_path)

      task_storage_reader = sqlite_reader.SQLiteStorageFileReader(
          task_storage_path)

      test_reader = merge_reader.StorageMergeReader(
          session, storage_writer, task_storage_reader, 'test_task')

      storage_writer.Open(path=task_storage_path)

      result = test_reader.MergeAttributeContainers()
      self.assertTrue(result)

      storage_writer.Close()

  def testMergeAttributeContainersWithDeserializationError(self):
    """Tests MergeAttributeContainers with a deserialization error."""
    session = sessions.Session()

    with shared_test_lib.TempDirectory() as temp_directory:
      task_storage_path = os.path.join(temp_directory, 'task.sqlite')
      self._CreateTaskStorageFile(
          task_storage_path, self._TEST_EVENTS_WITH_DESERIALIZATION_ERROR)

      session_storage_path = os.path.join(temp_directory, 'plaso.sqlite')
      storage_writer = sqlite_writer.SQLiteStorageFileWriter(
          session_storage_path)

      task_storage_reader = sqlite_reader.SQLiteStorageFileReader(
          task_storage_path)

      test_reader = merge_reader.StorageMergeReader(
          session, storage_writer, task_storage_reader, 'test_task')

      storage_writer.Open(path=task_storage_path)

      result = test_reader.MergeAttributeContainers()
      self.assertTrue(result)

      storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
