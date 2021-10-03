#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the fake (in-memory only) store."""

import unittest

from plaso.containers import events
from plaso.lib import definitions
from plaso.storage.fake import fake_store

from tests.storage import test_lib
from tests.containers import test_lib as containers_test_lib


class FakeStoreTest(test_lib.StorageTestCase):
  """Tests for the fake storage writer object."""

  # pylint: disable=protected-access

  # TODO: add tests for _RaiseIfNotReadable
  # TODO: add tests for _RaiseIfNotWritable

  def testWriteExistingAttributeContainer(self):
    """Tests the _WriteExistingAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    with self.assertRaises(IOError):
      test_store._WriteExistingAttributeContainer(event_data_stream)

    test_store._WriteNewAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store._WriteExistingAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

  def testWriteNewAttributeContainer(self):
    """Tests the _WriteNewAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store._WriteNewAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store.AddAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

    with self.assertRaises(IOError):
      test_store.AddAttributeContainer(event_data_stream)

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    test_store.AddAttributeContainer(event_data_stream)
    identifier = event_data_stream.GetIdentifier()

    container = test_store.GetAttributeContainerByIdentifier(
        event_data_stream.CONTAINER_TYPE, identifier)
    self.assertIsNotNone(container)

    identifier.sequence_number = 99

    container = test_store.GetAttributeContainerByIdentifier(
        event_data_stream.CONTAINER_TYPE, identifier)
    self.assertIsNone(container)

    test_store.Close()

  def testGetAttributeContainerByIndex(self):
    """Tests the GetAttributeContainerByIndex function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    container = test_store.GetAttributeContainerByIndex(
        event_data_stream.CONTAINER_TYPE, 0)
    self.assertIsNone(container)

    test_store.AddAttributeContainer(event_data_stream)

    container = test_store.GetAttributeContainerByIndex(
        event_data_stream.CONTAINER_TYPE, 0)
    self.assertIsNotNone(container)

    test_store.Close()

  def testGetAttributeContainers(self):
    """Tests the GetAttributeContainers function."""
    event_data_stream = events.EventDataStream()
    event_data_stream.md5_hash = '8f0bf95a7959baad9666b21a7feed79d'

    test_store = fake_store.FakeStore()
    test_store.Open()

    containers = list(test_store.GetAttributeContainers(
        event_data_stream.CONTAINER_TYPE))
    self.assertEqual(len(containers), 0)

    test_store.AddAttributeContainer(event_data_stream)

    containers = list(test_store.GetAttributeContainers(
        event_data_stream.CONTAINER_TYPE))
    self.assertEqual(len(containers), 1)

    filter_expression = 'md5_hash == "8f0bf95a7959baad9666b21a7feed79d"'
    containers = list(test_store.GetAttributeContainers(
        event_data_stream.CONTAINER_TYPE, filter_expression=filter_expression))
    self.assertEqual(len(containers), 1)

    filter_expression = 'md5_hash != "8f0bf95a7959baad9666b21a7feed79d"'
    containers = list(test_store.GetAttributeContainers(
        event_data_stream.CONTAINER_TYPE, filter_expression=filter_expression))
    self.assertEqual(len(containers), 0)

    test_store.Close()

  def testGetNumberOfAttributeContainers(self):
    """Tests the GetNumberOfAttributeContainers function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    test_store.AddAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()

  def testGetEventTagByEventIdentifier(self):
    """Tests the GetEventTagByEventIdentifier function."""
    test_store = fake_store.FakeStore()
    test_store.Open()

    index = 0
    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      test_store.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(
          event_data_stream.GetIdentifier())
      test_store.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      test_store.AddAttributeContainer(event)

      if index == 1:
        event_tag = events.EventTag()
        event_tag.AddLabels(['Malware', 'Benign'])

        event_identifier = event.GetIdentifier()
        event_tag.SetEventIdentifier(event_identifier)
        test_store.AddAttributeContainer(event_tag)

      index += 1

    # Do not close and reopen the fake store.

    test_event = test_store.GetAttributeContainerByIndex(
        events.EventObject.CONTAINER_TYPE, 1)
    self.assertIsNotNone(test_event)

    test_event_identifier = test_event.GetIdentifier()
    self.assertIsNotNone(test_event_identifier)

    test_event_tag = test_store.GetEventTagByEventIdentifier(
        test_event_identifier)
    self.assertIsNotNone(test_event_tag)

    self.assertEqual(test_event_tag.labels, ['Malware', 'Benign'])

    test_store.Close()

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

  def testHasAttributeContainers(self):
    """Tests the HasAttributeContainers function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    result = test_store.HasAttributeContainers(event_data_stream.CONTAINER_TYPE)
    self.assertFalse(result)

    test_store.AddAttributeContainer(event_data_stream)

    result = test_store.HasAttributeContainers(event_data_stream.CONTAINER_TYPE)
    self.assertTrue(result)

    test_store.Close()

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

  def testUpdateAttributeContainer(self):
    """Tests the UpdateAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    test_store = fake_store.FakeStore()
    test_store.Open()

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 0)

    with self.assertRaises(IOError):
      test_store.UpdateAttributeContainer(event_data_stream)

    test_store.AddAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.UpdateAttributeContainer(event_data_stream)

    number_of_containers = test_store.GetNumberOfAttributeContainers(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(number_of_containers, 1)

    test_store.Close()


if __name__ == '__main__':
  unittest.main()
