#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the fake storage writer."""

import unittest

from plaso.containers import events
from plaso.lib import definitions
from plaso.storage.fake import writer as fake_writer

from tests.storage import test_lib
from tests.containers import test_lib as containers_test_lib


class FakeStorageWriterTest(test_lib.StorageTestCase):
  """Tests for the fake storage writer."""

  # pylint: disable=protected-access

  def _AddTestEvents(self, storage_writer):
    """Adds tests events to the storage writer.

    Args:
      storage_writer (FakeStorageWriter): storage writer.

    Returns:
      list[EventObject]: test events.
    """
    test_events = []
    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      storage_writer.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_writer.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddAttributeContainer(event)

      test_events.append(event)

    return test_events

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      storage_writer.AddAttributeContainer(event_data_stream)

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_data_stream.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

    finally:
      storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddAttributeContainer(event_data_stream)

  def testAddOrUpdateEventTag(self):
    """Tests the AddOrUpdateEventTag function."""
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      test_events = self._AddTestEvents(storage_writer)

      event_tag = events.EventTag()
      event_identifier = test_events[1].GetIdentifier()
      event_tag.SetEventIdentifier(event_identifier)

      event_tag.AddLabel('Label1')

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      storage_writer.AddOrUpdateEventTag(event_tag)

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      event_tag = events.EventTag()
      event_identifier = test_events[2].GetIdentifier()
      event_tag.SetEventIdentifier(event_identifier)

      event_tag.AddLabel('Label2')

      storage_writer.AddOrUpdateEventTag(event_tag)

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 2)

      event_tag = events.EventTag()
      event_identifier = test_events[1].GetIdentifier()
      event_tag.SetEventIdentifier(event_identifier)

      event_tag.AddLabel('AnotherLabel1')

      storage_writer.AddOrUpdateEventTag(event_tag)

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 2)

      event_tags = list(storage_writer.GetAttributeContainers(
          event_tag.CONTAINER_TYPE))
      self.assertEqual(event_tags[0].labels, ['Label1', 'AnotherLabel1'])
      self.assertEqual(event_tags[1].labels, ['Label2'])

    finally:
      storage_writer.Close()

  # TODO: add tests for GetFirstWrittenEventSource
  # TODO: add tests for GetNextWrittenEventSource

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      self._AddTestEvents(storage_writer)

      test_events = list(storage_writer.GetSortedEvents())
      self.assertEqual(len(test_events), 4)

    finally:
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
