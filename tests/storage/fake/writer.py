#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the fake storage writer."""

import unittest

from plaso.lib import definitions
from plaso.storage.fake import writer as fake_writer

from tests.storage import test_lib
from tests.containers import test_lib as containers_test_lib


class FakeStorageWriterTest(test_lib.StorageTestCase):
  """Tests for the fake storage writer."""

  # pylint: disable=protected-access

  # TODO: add tests for GetFirstWrittenEventSource
  # TODO: add tests for GetNextWrittenEventSource

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      storage_writer.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_writer.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddAttributeContainer(event)

    test_events = list(storage_writer.GetSortedEvents())
    self.assertEqual(len(test_events), 4)

    storage_writer.Close()

    # TODO: add test with time range.

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    storage_writer.Close()

    storage_writer.Open()
    storage_writer.Close()

    storage_writer = fake_writer.FakeStorageWriter(
        storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open()
    storage_writer.Close()

    storage_writer.Open()

    with self.assertRaises(IOError):
      storage_writer.Open()

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
