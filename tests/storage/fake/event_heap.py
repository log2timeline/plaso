#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the heaps to sort events in chronological order."""

import unittest

from plaso.lib import definitions
from plaso.storage.fake import event_heap

from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class EventHeapTest(test_lib.StorageTestCase):
  """Tests for the event heap."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'timestamp': 5134324321,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN},
      {'data_type': 'test:event',
       'timestamp': 2345871286,
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN}]

  def testNumberOfEvents(self):
    """Tests the number_of_events property."""
    test_heap = event_heap.EventHeap()
    self.assertEqual(test_heap.number_of_events, 0)

  def testPopEvent(self):
    """Tests the PopEvent function."""
    test_heap = event_heap.EventHeap()

    self.assertEqual(len(test_heap._heap), 0)

    test_event = test_heap.PopEvent()
    self.assertIsNone(test_event)

    event_index = 0
    for event, _, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_heap.PushEvent(event, event_index)
      event_index += 1

    self.assertEqual(len(test_heap._heap), 2)

    test_event = test_heap.PopEvent()
    self.assertIsNotNone(test_event)

    self.assertEqual(len(test_heap._heap), 1)

  def testPopEvents(self):
    """Tests the PopEvents function."""
    test_heap = event_heap.EventHeap()

    self.assertEqual(len(test_heap._heap), 0)

    test_events = list(test_heap.PopEvents())
    self.assertEqual(len(test_events), 0)

    event_index = 0
    for event, _, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      test_heap.PushEvent(event, event_index)
      event_index += 1

    self.assertEqual(len(test_heap._heap), 2)

    test_events = list(test_heap.PopEvents())
    self.assertEqual(len(test_events), 2)

    self.assertEqual(len(test_heap._heap), 0)

  def testPushEvent(self):
    """Tests the PushEvent function."""
    test_heap = event_heap.EventHeap()

    self.assertEqual(len(test_heap._heap), 0)

    event, _, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    test_heap.PushEvent(event, 0)

    self.assertEqual(len(test_heap._heap), 1)


if __name__ == '__main__':
  unittest.main()
