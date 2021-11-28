#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event tag index."""

import os
import unittest

from plaso.storage import event_tag_index
from plaso.storage import identifiers
from plaso.storage.sqlite import reader as sqlite_file_reader
from plaso.storage.sqlite import sqlite_file

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class EventTagIndexTest(test_lib.StorageTestCase):
  """Tests for the event tag index."""

  # pylint: disable=protected-access

  def _AddTestEvents(self, storage_file):
    """Adds tests events to the storage file.

    Args:
      storage_file (SQLiteStorageFile): storage file.

    Returns:
      list[EventObject]: test events.
    """
    test_events = []
    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      storage_file.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_file.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_file.AddAttributeContainer(event)

      test_events.append(event)

    return test_events

  def _CreateTestStorageFileWithTags(self, path):
    """Creates a storage file with event tags for testing.

    Args:
      path (str): path of the storage file.
    """
    storage_file = sqlite_file.SQLiteStorageFile()
    storage_file.Open(path=path, read_only=False)

    try:
      test_events = self._AddTestEvents(storage_file)

      test_event_tags = self._CreateTestEventTags(test_events)
      for event_tag in test_event_tags[:-1]:
        storage_file.AddAttributeContainer(event_tag)
      for event_tag in test_event_tags[-1:]:
        storage_file.AddAttributeContainer(event_tag)

    finally:
      storage_file.Close()

  def testBuild(self):
    """Tests the _Build function."""
    test_index = event_tag_index.EventTagIndex()

    self.assertIsNone(test_index._index)

    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    storage_reader = sqlite_file_reader.SQLiteStorageFileReader(
        test_file_path)

    try:
      test_index._Build(storage_reader)
    finally:
      storage_reader.Close()

    self.assertIsNotNone(test_index._index)

  def testGetEventTagByIdentifier(self):
    """Tests the GetEventTagByIdentifier function."""
    test_index = event_tag_index.EventTagIndex()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_reader = sqlite_file_reader.SQLiteStorageFileReader(
          temp_file)

      try:
        event_identifier = identifiers.SQLTableIdentifier('event', 1)
        event_tag = test_index.GetEventTagByIdentifier(
            storage_reader, event_identifier)
        self.assertIsNotNone(event_tag)

        event_identifier = identifiers.SQLTableIdentifier('event', 99)
        event_tag = test_index.GetEventTagByIdentifier(
            storage_reader, event_identifier)
        self.assertIsNone(event_tag)

      finally:
        storage_reader.Close()

  # TODO: add test for SetEventTag.


if __name__ == '__main__':
  unittest.main()
