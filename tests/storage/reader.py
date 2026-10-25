#!/usr/bin/env python3
"""Tests for the storage reader."""

import unittest

from acstore.containers import interface as containers_interface

from plaso.containers import event_sources
from plaso.containers import sessions
from plaso.storage import reader
from plaso.storage import time_range as storage_time_range
from plaso.storage.fake import fake_store

from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class StorageReaderTest(test_lib.StorageTestCase):
    """Tests for the storage reader."""

    # pylint: disable=protected-access

    def testInitialization(self):
        """Tests the __init__ function."""
        test_reader = reader.StorageReader()
        self.assertIsNotNone(test_reader)

    def testEnterExit(self):
        """Tests the __enter__ and __exit__ functions."""
        test_store = fake_store.FakeStore()

        with reader.StorageReader() as test_reader:
            self.assertIsInstance(test_reader, reader.StorageReader)

            test_reader._store = test_store
            test_reader._store.Open()

        self.assertIsNone(test_reader._store)

        # The underlying store is closed on exit.
        with self.assertRaises(OSError):
            test_store.Close()

    # TODO: add tests for Close

    def testGetAttributeContainerByIdentifier(self):
        """Tests the GetAttributeContainerByIdentifier function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()
        test_reader._store.Open()

        try:
            event_source = event_sources.EventSource()
            test_reader._store.AddAttributeContainer(event_source)

            test_identifier = event_source.GetIdentifier()
            test_container = test_reader.GetAttributeContainerByIdentifier(
                event_source.CONTAINER_TYPE, test_identifier
            )
            self.assertIsNotNone(test_container)

            test_identifier = containers_interface.AttributeContainerIdentifier(
                name=event_source.CONTAINER_TYPE, sequence_number=99
            )
            test_container = test_reader.GetAttributeContainerByIdentifier(
                event_source.CONTAINER_TYPE, test_identifier
            )
            self.assertIsNone(test_container)

        finally:
            test_reader._store.Close()

    def testGetAttributeContainerByIndex(self):
        """Tests the GetAttributeContainerByIndex function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()
        test_reader._store.Open()

        try:
            event_source = event_sources.EventSource()
            test_reader._store.AddAttributeContainer(event_source)

            test_container = test_reader.GetAttributeContainerByIndex(
                event_source.CONTAINER_TYPE, 0
            )
            self.assertIsNotNone(test_container)

            test_container = test_reader.GetAttributeContainerByIndex(
                event_source.CONTAINER_TYPE, 99
            )
            self.assertIsNone(test_container)

        finally:
            test_reader._store.Close()

    def testGetAttributeContainers(self):
        """Tests the GetAttributeContainers function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()
        test_reader._store.Open()

        try:
            event_source = event_sources.EventSource()
            test_reader._store.AddAttributeContainer(event_source)

            test_generator = test_reader.GetAttributeContainers(
                event_source.CONTAINER_TYPE
            )
            test_containers = list(test_generator)
            self.assertEqual(len(test_containers), 1)

        finally:
            test_reader._store.Close()

    def testGetFormatVersion(self):
        """Tests the GetFormatVersion function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()

        format_version = test_reader.GetFormatVersion()
        self.assertIsNone(format_version)

    def testGetNumberOfAttributeContainers(self):
        """Tests the GetNumberOfAttributeContainers function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()
        test_reader._store.Open()

        try:
            event_source = event_sources.EventSource()
            test_reader._store.AddAttributeContainer(event_source)

            number_of_containers = test_reader.GetNumberOfAttributeContainers(
                event_source.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

        finally:
            test_reader._store.Close()

    def testGetSerializationFormat(self):
        """Tests the GetSerializationFormat function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()

        serialization_format = test_reader.GetSerializationFormat()
        self.assertIsNone(serialization_format)

    def testGetSessions(self):
        """Tests the GetSessions function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()
        test_reader._store.Open()

        try:
            test_sessions = list(test_reader.GetSessions())
            self.assertEqual(len(test_sessions), 0)

            session = sessions.Session()
            test_reader._store.AddAttributeContainer(session)

            event_source = event_sources.EventSource()
            test_reader._store.AddAttributeContainer(event_source)

            test_sessions = list(test_reader.GetSessions())
            self.assertEqual(len(test_sessions), 1)
            self.assertEqual(test_sessions[0].CONTAINER_TYPE, session.CONTAINER_TYPE)
            self.assertEqual(test_sessions[0].identifier, session.identifier)

        finally:
            test_reader._store.Close()

    def testGetSortedEvents(self):
        """Tests the GetSortedEvents function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()
        test_reader._store.Open()

        try:
            for event, _, _ in containers_test_lib.CreateEventsFromValues(
                self._TEST_EVENTS
            ):
                test_reader._store.AddAttributeContainer(event)

            test_events = list(test_reader.GetSortedEvents())
            timestamps = [event.timestamp for event in test_events]
            self.assertEqual(
                timestamps,
                [
                    1238934459000000,
                    1334940286000000,
                    1334961526929596,
                    1334966206929596,
                ],
            )

            time_range = storage_time_range.TimeRange(
                1334940286000000, 1334961526929596
            )
            test_events = list(test_reader.GetSortedEvents(time_range=time_range))
            timestamps = [event.timestamp for event in test_events]
            self.assertEqual(timestamps, [1334940286000000, 1334961526929596])

        finally:
            test_reader._store.Close()

    def testHasAttributeContainers(self):
        """Tests the HasAttributeContainers function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()
        test_reader._store.Open()

        try:
            event_source = event_sources.EventSource()
            test_reader._store.AddAttributeContainer(event_source)

            result = test_reader.HasAttributeContainers(event_source.CONTAINER_TYPE)
            self.assertTrue(result)

        finally:
            test_reader._store.Close()

    def testSetSerializersProfiler(self):
        """Tests the SetSerializersProfiler function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()

        test_reader.SetSerializersProfiler(None)

    def testSetStorageProfiler(self):
        """Tests the SetStorageProfiler function."""
        test_reader = reader.StorageReader()
        test_reader._store = fake_store.FakeStore()

        test_reader.SetStorageProfiler(None)


if __name__ == "__main__":
    unittest.main()
