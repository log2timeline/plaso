#!/usr/bin/env python3
"""Tests for the fake storage writer."""

import collections
import unittest

from plaso.containers import event_sources
from plaso.containers import events
from plaso.lib import definitions
from plaso.storage import time_range as storage_time_range
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
        for (
            event,
            event_data,
            event_data_stream,
        ) in containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS):
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
                event_data_stream.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 0)

            storage_writer.AddAttributeContainer(event_data_stream)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_data_stream.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

        finally:
            storage_writer.Close()

        with self.assertRaises(OSError):
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

            event_tag.AddLabel("Label1")

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_tag.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 0)

            storage_writer.AddOrUpdateEventTag(event_tag)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_tag.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

            event_tag = events.EventTag()
            event_identifier = test_events[2].GetIdentifier()
            event_tag.SetEventIdentifier(event_identifier)

            event_tag.AddLabel("Label2")

            storage_writer.AddOrUpdateEventTag(event_tag)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_tag.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 2)

            event_tag = events.EventTag()
            event_identifier = test_events[1].GetIdentifier()
            event_tag.SetEventIdentifier(event_identifier)

            event_tag.AddLabel("AnotherLabel1")

            storage_writer.AddOrUpdateEventTag(event_tag)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_tag.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 2)

            event_tags = list(
                storage_writer.GetAttributeContainers(event_tag.CONTAINER_TYPE)
            )
            self.assertEqual(event_tags[0].labels, ["Label1", "AnotherLabel1"])
            self.assertEqual(event_tags[1].labels, ["Label2"])

        finally:
            storage_writer.Close()

    def testGetFirstWrittenEventSource(self):
        """Tests the GetFirstWrittenEventSource function."""
        storage_writer = fake_writer.FakeStorageWriter()

        with self.assertRaises(OSError):
            storage_writer.GetFirstWrittenEventSource()

        storage_writer.Open()

        try:
            event_source = storage_writer.GetFirstWrittenEventSource()
            self.assertIsNone(event_source)

            first_event_source = event_sources.EventSource(file_entry_type="file")
            storage_writer.AddAttributeContainer(first_event_source)

            second_event_source = event_sources.EventSource(file_entry_type="directory")
            storage_writer.AddAttributeContainer(second_event_source)

            event_source = storage_writer.GetFirstWrittenEventSource()
            self.assertIsNotNone(event_source)
            self.assertEqual(event_source.file_entry_type, "file")

            # GetFirstWrittenEventSource resets the position of
            # GetNextWrittenEventSource.
            storage_writer.GetNextWrittenEventSource()
            event_source = storage_writer.GetFirstWrittenEventSource()
            self.assertEqual(event_source.file_entry_type, "file")

            event_source = storage_writer.GetNextWrittenEventSource()
            self.assertEqual(event_source.file_entry_type, "directory")

        finally:
            storage_writer.Close()

    def testGetNextWrittenEventSource(self):
        """Tests the GetNextWrittenEventSource function."""
        storage_writer = fake_writer.FakeStorageWriter()

        with self.assertRaises(OSError):
            storage_writer.GetNextWrittenEventSource()

        storage_writer.Open()

        try:
            first_event_source = event_sources.EventSource(file_entry_type="file")
            storage_writer.AddAttributeContainer(first_event_source)

            second_event_source = event_sources.EventSource(file_entry_type="directory")
            storage_writer.AddAttributeContainer(second_event_source)

            event_source = storage_writer.GetFirstWrittenEventSource()
            self.assertEqual(event_source.file_entry_type, "file")

            event_source = storage_writer.GetNextWrittenEventSource()
            self.assertIsNotNone(event_source)
            self.assertEqual(event_source.file_entry_type, "directory")

            event_source = storage_writer.GetNextWrittenEventSource()
            self.assertIsNone(event_source)

        finally:
            storage_writer.Close()

    def testGetSortedEvents(self):
        """Tests the GetSortedEvents function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            self._AddTestEvents(storage_writer)

            test_events = list(storage_writer.GetSortedEvents())
            self.assertEqual(len(test_events), 4)

            time_range = storage_time_range.TimeRange(
                1334940286000000, 1334961526929596
            )
            test_events = list(storage_writer.GetSortedEvents(time_range=time_range))
            timestamps = [event.timestamp for event in test_events]
            self.assertEqual(timestamps, [1334940286000000, 1334961526929596])

        finally:
            storage_writer.Close()

    def testUpdateDataTypesCounter(self):
        """Tests the UpdateDataTypesCounter function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            stored_data_types_counter = storage_writer.GetDataTypesCounter()
            self.assertEqual(len(stored_data_types_counter), 0)

            data_types_counter = collections.Counter({"fs:stat": 5, "total": 5})
            storage_writer.UpdateDataTypesCounter(
                stored_data_types_counter, data_types_counter
            )
            self.assertEqual(data_types_counter["fs:stat"], 5)

            data_types_counter = collections.Counter({"fs:stat": 3, "total": 3})
            storage_writer.UpdateDataTypesCounter(
                stored_data_types_counter, data_types_counter
            )
            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                "data_type_count"
            )
            self.assertEqual(number_of_containers, 2)

            stored_data_types_counter = storage_writer.GetDataTypesCounter()
            self.assertEqual(stored_data_types_counter["fs:stat"].number_of_events, 8)
            self.assertEqual(stored_data_types_counter["total"].number_of_events, 8)

        finally:
            storage_writer.Close()

    def testUpdateEventLabelsCounter(self):
        """Tests the UpdateEventLabelsCounter function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            stored_event_labels_counter = storage_writer.GetEventLabelsCounter()
            self.assertEqual(len(stored_event_labels_counter), 0)

            event_labels_counter = collections.Counter({"corrupted": 5, "total": 5})
            storage_writer.UpdateEventLabelsCounter(
                stored_event_labels_counter, event_labels_counter
            )
            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                "event_label_count"
            )
            self.assertEqual(number_of_containers, 2)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                "parser_count"
            )
            self.assertEqual(number_of_containers, 0)

            stored_event_labels_counter = storage_writer.GetEventLabelsCounter()
            self.assertEqual(
                stored_event_labels_counter["corrupted"].number_of_events, 5
            )
            event_labels_counter = collections.Counter({"corrupted": 3, "total": 3})

            storage_writer.UpdateEventLabelsCounter(
                stored_event_labels_counter, event_labels_counter
            )
            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                "event_label_count"
            )
            self.assertEqual(number_of_containers, 2)

            stored_event_labels_counter = storage_writer.GetEventLabelsCounter()
            self.assertEqual(
                stored_event_labels_counter["corrupted"].number_of_events, 8
            )
            self.assertEqual(stored_event_labels_counter["total"].number_of_events, 8)

            event_labels_counter = collections.Counter({"recovered": 2, "total": 2})
            storage_writer.UpdateEventLabelsCounter(
                stored_event_labels_counter, event_labels_counter
            )
            self.assertEqual(event_labels_counter["recovered"], 2)

            event_labels_counter = collections.Counter({"recovered": 1, "total": 1})
            storage_writer.UpdateEventLabelsCounter(
                stored_event_labels_counter, event_labels_counter
            )
            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                "event_label_count"
            )
            self.assertEqual(number_of_containers, 3)

            stored_event_labels_counter = storage_writer.GetEventLabelsCounter()
            self.assertEqual(
                stored_event_labels_counter["recovered"].number_of_events, 3
            )
            self.assertEqual(stored_event_labels_counter["total"].number_of_events, 11)

        finally:
            storage_writer.Close()

    def testUpdateParsersCounter(self):
        """Tests the UpdateParsersCounter function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            stored_parsers_counter = storage_writer.GetParsersCounter()
            self.assertEqual(len(stored_parsers_counter), 0)

            parsers_counter = collections.Counter({"filestat": 5, "total": 5})
            storage_writer.UpdateParsersCounter(stored_parsers_counter, parsers_counter)
            self.assertEqual(parsers_counter["filestat"], 5)

            parsers_counter = collections.Counter({"filestat": 3, "total": 3})
            storage_writer.UpdateParsersCounter(stored_parsers_counter, parsers_counter)
            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                "parser_count"
            )
            self.assertEqual(number_of_containers, 2)

            stored_parsers_counter = storage_writer.GetParsersCounter()
            self.assertEqual(stored_parsers_counter["filestat"].number_of_events, 8)
            self.assertEqual(stored_parsers_counter["total"].number_of_events, 8)

        finally:
            storage_writer.Close()

    def testOpenClose(self):
        """Tests the Open and Close functions."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        storage_writer.Close()

        storage_writer.Open()
        storage_writer.Close()

        storage_writer = fake_writer.FakeStorageWriter(
            storage_type=definitions.STORAGE_TYPE_TASK
        )
        storage_writer.Open()
        storage_writer.Close()

        storage_writer.Open()

        with self.assertRaises(OSError):
            storage_writer.Open()

        storage_writer.Close()

        with self.assertRaises(OSError):
            storage_writer.Close()


if __name__ == "__main__":
    unittest.main()
