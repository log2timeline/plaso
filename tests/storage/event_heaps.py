#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the heaps to sort events in chronological order.."""

from __future__ import unicode_literals

import os
import unittest

from plaso.storage import event_heaps
from plaso.storage import zip_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


# TODO: add tests for SerializedEventHeap


class SerializedStreamEventHeapTest(test_lib.StorageTestCase):
  """Tests for the event heap for serialized stream storage."""

  # pylint: disable=protected-access

  def testNumberOfEvents(self):
    """Tests the number_of_events property."""
    event_heap = event_heaps.SerializedStreamEventHeap()
    self.assertEqual(event_heap.number_of_events, 0)

  # TODO: add tests for PeekEvent.

  def testPopEvent(self):
    """Tests the PopEvent function."""
    event_heap = event_heaps.SerializedStreamEventHeap()

    test_event = event_heap.PopEvent()
    self.assertEqual(test_event, (None, None))

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      test_events = self._CreateTestEvents()
      for event in test_events:
        storage_file.AddEvent(event)
        event_heap.PushEvent(event)

      test_event, stream_number = event_heap.PopEvent()
      self.assertEqual(test_event, test_events[3])
      self.assertEqual(stream_number, 1)

      test_event, _ = event_heap.PopEvent()
      self.assertEqual(test_event, test_events[2])

      test_event, _ = event_heap.PopEvent()
      self.assertEqual(test_event, test_events[0])

      test_event, _ = event_heap.PopEvent()
      self.assertEqual(test_event, test_events[1])

  def testPopEvents(self):
    """Tests the PopEvents function."""
    event_heap = event_heaps.SerializedStreamEventHeap()

    test_events = list(event_heap.PopEvents())
    self.assertEqual(len(test_events), 0)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      test_events = self._CreateTestEvents()
      for event in test_events:
        storage_file.AddEvent(event)
        event_heap.PushEvent(event)

      test_events = list(event_heap.PopEvents())
      self.assertEqual(len(test_events), 4)

  def testPushEvent(self):
    """Tests the PushEvent function."""
    event_heap = event_heaps.SerializedStreamEventHeap()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      test_events = self._CreateTestEvents()
      for event in test_events:
        storage_file.AddEvent(event)
        event_heap.PushEvent(event)

      self.assertEqual(event_heap.number_of_events, 4)

  def testPushEvents(self):
    """Tests the PushEvents function."""
    event_heap = event_heaps.SerializedStreamEventHeap()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      test_events = self._CreateTestEvents()
      for event in test_events:
        storage_file.AddEvent(event)

      event_heap.PushEvents(test_events)

      self.assertEqual(event_heap.number_of_events, 4)


if __name__ == '__main__':
  unittest.main()
