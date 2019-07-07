#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event tag index."""

from __future__ import unicode_literals

import os
import unittest

from plaso.storage import event_tag_index
from plaso.storage import identifiers
from plaso.storage.sqlite import sqlite_file

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class EventTagIndexTest(test_lib.StorageTestCase):
  """Tests for the event tag index."""

  # pylint: disable=protected-access

  def _CreateTestStorageFileWithTags(self, path):
    """Creates a storage file with event tags for testing.

    Args:
      path (str): path of the storage file.
    """
    storage_file = sqlite_file.SQLiteStorageFile()
    storage_file.Open(path=path, read_only=False)

    test_events = []
    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      storage_file.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_file.AddEvent(event)

      test_events.append(event)

    test_event_tags = self._CreateTestEventTags(test_events)
    for event_tag in test_event_tags[:-1]:
      storage_file.AddEventTag(event_tag)
    for event_tag in test_event_tags[-1:]:
      storage_file.AddEventTag(event_tag)

    storage_file.Close()

  def testBuild(self):
    """Tests the _Build function."""
    test_index = event_tag_index.EventTagIndex()

    self.assertIsNone(test_index._index)

    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    storage_file = sqlite_file.SQLiteStorageFile()
    storage_file.Open(path=test_file_path)
    test_index._Build(storage_file)
    storage_file.Close()

    self.assertIsNotNone(test_index._index)

  def testGetEventTagByIdentifier(self):
    """Tests the GetEventTagByIdentifier function."""
    test_index = event_tag_index.EventTagIndex()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      event_identifier = identifiers.SQLTableIdentifier('event', 1)
      event_tag = test_index.GetEventTagByIdentifier(
          storage_file, event_identifier)
      self.assertIsNotNone(event_tag)
      self.assertEqual(event_tag.comment, 'My comment')

      event_identifier = identifiers.SQLTableIdentifier('event', 99)
      event_tag = test_index.GetEventTagByIdentifier(
          storage_file, event_identifier)
      self.assertIsNone(event_tag)

      storage_file.Close()

  # TODO: add test for SetEventTag.


if __name__ == '__main__':
  unittest.main()
