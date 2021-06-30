#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ake (in-memory only) store."""

import unittest

from plaso.containers import event_sources
from plaso.lib import definitions
from plaso.storage.fake import fake_store

from tests.storage import test_lib
from tests.containers import test_lib as containers_test_lib


class FakeStoreTest(test_lib.StorageTestCase):
  """Tests for the fake storage writer object."""

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer function."""
    event_source = event_sources.EventSource()

    test_store = fake_store.FakeStore()
    test_store.Open()

    test_store.AddAttributeContainer(event_source)

    test_store.Close()

    with self.assertRaises(IOError):
      test_store.AddAttributeContainer(event_source)

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    test_store = fake_store.FakeStore()
    test_store.Open()
    test_store.Close()

    test_store.Open()
    test_store.Close()

    test_store = fake_store.FakeStore(
        storage_type=definitions.STORAGE_TYPE_TASK)
    test_store.Open()
    test_store.Close()

    test_store.Open()

    with self.assertRaises(IOError):
      test_store.Open()

    test_store.Close()

    with self.assertRaises(IOError):
      test_store.Close()

  # TODO: add tests for GetFirstWrittenEventSource and
  # GetNextWrittenEventSource.

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    test_store = fake_store.FakeStore()
    test_store.Open()

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      test_store.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      test_store.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      test_store.AddAttributeContainer(event)

    test_events = list(test_store.GetSortedEvents())
    self.assertEqual(len(test_events), 4)

    test_store.Close()

    # TODO: add test with time range.


if __name__ == '__main__':
  unittest.main()
