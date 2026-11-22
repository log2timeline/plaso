#!/usr/bin/env python3
"""Tests for the storage writer."""

import unittest

from plaso.containers import events
from plaso.lib import definitions
from plaso.storage import writer
from plaso.storage.fake import fake_store

from tests.storage import test_lib


class StorageWriterTest(test_lib.StorageTestCase):
    """Tests for the storage writer."""

    # pylint: disable=protected-access

    def testRaiseIfNotWritable(self):
        """Tests the _RaiseIfNotWritable function."""
        storage_writer = writer.StorageWriter()

        with self.assertRaises(OSError):
            storage_writer._RaiseIfNotWritable()

    def testAddAttributeContainer(self):
        """Tests the AddAttributeContainer function."""
        event_data_stream = events.EventDataStream()

        storage_writer = writer.StorageWriter()

        with self.assertRaises(OSError):
            storage_writer.AddAttributeContainer(event_data_stream)

        storage_writer._store = fake_store.FakeStore()
        storage_writer._store.Open()

        try:
            storage_writer.AddAttributeContainer(event_data_stream)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_data_stream.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

            self.assertEqual(
                storage_writer._attribute_containers_counter[
                    event_data_stream.CONTAINER_TYPE
                ],
                1,
            )

        finally:
            storage_writer.Close()

    def testAddOrUpdateEventTag(self):
        """Tests the AddOrUpdateEventTag function."""
        event_tag = events.EventTag()

        storage_writer = writer.StorageWriter()

        with self.assertRaises(OSError):
            storage_writer.AddOrUpdateEventTag(event_tag)

        storage_writer = writer.StorageWriter(
            storage_type=definitions.STORAGE_TYPE_TASK
        )
        storage_writer._store = fake_store.FakeStore()
        storage_writer._store.Open()

        try:
            event = events.EventObject()
            storage_writer.AddAttributeContainer(event)

            event_tag.SetEventIdentifier(event.GetIdentifier())
            event_tag.AddLabel("Label1")

            storage_writer.AddOrUpdateEventTag(event_tag)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_tag.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

            event_tag = events.EventTag()
            event_tag.SetEventIdentifier(event.GetIdentifier())
            event_tag.AddLabel("Label2")

            storage_writer.AddOrUpdateEventTag(event_tag)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_tag.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

            # A task storage writer also counts updated event tags.
            self.assertEqual(
                storage_writer._attribute_containers_counter[event_tag.CONTAINER_TYPE],
                2,
            )

            stored_event_tag = storage_writer.GetEventTagByEventIdentifier(
                event.GetIdentifier()
            )
            self.assertEqual(stored_event_tag.labels, ["Label1", "Label2"])

        finally:
            storage_writer.Close()

    def testClose(self):
        """Tests the Close function."""
        storage_writer = writer.StorageWriter()
        test_store = fake_store.FakeStore()
        storage_writer._store = test_store
        storage_writer._store.Open()

        storage_writer.Close()
        self.assertIsNone(storage_writer._store)

        # The underlying store is closed as well.
        with self.assertRaises(OSError):
            test_store.Close()

        with self.assertRaises(OSError):
            storage_writer.Close()

    def testUpdateAttributeContainer(self):
        """Tests the UpdateAttributeContainer function."""
        event_data_stream = events.EventDataStream()

        storage_writer = writer.StorageWriter()

        with self.assertRaises(OSError):
            storage_writer.UpdateAttributeContainer(event_data_stream)

        storage_writer._store = fake_store.FakeStore()
        storage_writer._store.Open()

        try:
            storage_writer.AddAttributeContainer(event_data_stream)

            event_data_stream.md5_hash = "8f0bf95a7959baad9666b21a7feed79d"
            storage_writer.UpdateAttributeContainer(event_data_stream)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                event_data_stream.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

            stored_event_data_stream = storage_writer.GetAttributeContainerByIndex(
                event_data_stream.CONTAINER_TYPE, 0
            )
            self.assertEqual(
                stored_event_data_stream.md5_hash, "8f0bf95a7959baad9666b21a7feed79d"
            )

        finally:
            storage_writer.Close()


if __name__ == "__main__":
    unittest.main()
