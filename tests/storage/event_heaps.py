#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the heaps to sort events in chronological order."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.storage import event_heaps

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
    event_heap = event_heaps.EventHeap()
    self.assertEqual(event_heap.number_of_events, 0)

  def testPopEvent(self):
    """Tests the PopEvent function."""
    event_heap = event_heaps.EventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    test_event = event_heap.PopEvent()
    self.assertIsNone(test_event)

    event_index = 0
    for event, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      event_heap.PushEvent(event, event_index)
      event_index += 1

    self.assertEqual(len(event_heap._heap), 2)

    test_event = event_heap.PopEvent()
    self.assertIsNotNone(test_event)

    self.assertEqual(len(event_heap._heap), 1)

  def testPopEvents(self):
    """Tests the PopEvents function."""
    event_heap = event_heaps.EventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    test_events = list(event_heap.PopEvents())
    self.assertEqual(len(test_events), 0)

    event_index = 0
    for event, _ in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      event_heap.PushEvent(event, event_index)
      event_index += 1

    self.assertEqual(len(event_heap._heap), 2)

    test_events = list(event_heap.PopEvents())
    self.assertEqual(len(test_events), 2)

    self.assertEqual(len(event_heap._heap), 0)

  def testPushEvent(self):
    """Tests the PushEvent function."""
    event_heap = event_heaps.EventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    event, _ = containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
    event_heap.PushEvent(event, 0)

    self.assertEqual(len(event_heap._heap), 1)


class SerializedEventHeapTest(test_lib.StorageTestCase):
  """Tests for the serialized event heap."""

  # pylint: disable=protected-access

  def testNumberOfEvents(self):
    """Tests the number_of_events property."""
    event_heap = event_heaps.SerializedEventHeap()
    self.assertEqual(event_heap.number_of_events, 0)

  def testEmpty(self):
    """Tests the Empty function."""
    event_heap = event_heaps.SerializedEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    event_heap.PushEvent(5134324321, b'event_data1')
    event_heap.PushEvent(2345871286, b'event_data2')

    self.assertEqual(len(event_heap._heap), 2)

    event_heap.Empty()
    self.assertEqual(len(event_heap._heap), 0)
    self.assertEqual(event_heap.data_size, 0)

  def testPopEvent(self):
    """Tests the PopEvent function."""
    event_heap = event_heaps.SerializedEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    test_timestamp, test_event_data = event_heap.PopEvent()
    self.assertIsNone(test_timestamp)
    self.assertIsNone(test_event_data)

    event_heap.PushEvent(5134324321, b'event_data1')
    event_heap.PushEvent(2345871286, b'event_data2')

    self.assertEqual(len(event_heap._heap), 2)

    test_timestamp, test_event_data = event_heap.PopEvent()
    self.assertEqual(test_timestamp, 2345871286)
    self.assertEqual(test_event_data, b'event_data2')

    self.assertEqual(len(event_heap._heap), 1)

  def testPushEvent(self):
    """Tests the PushEvent function."""
    event_heap = event_heaps.SerializedEventHeap()

    self.assertEqual(len(event_heap._heap), 0)

    event_heap.PushEvent(5134324321, b'event_data1')

    self.assertEqual(len(event_heap._heap), 1)


if __name__ == '__main__':
  unittest.main()
