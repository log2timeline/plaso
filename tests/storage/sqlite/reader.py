#!/usr/bin/env python3
"""Tests for the SQLite-based storage reader."""

import unittest

from acstore.containers import interface as containers_interface

from plaso.containers import events
from plaso.storage.sqlite import reader

from tests.storage import test_lib


class SQLiteStorageReaderTest(test_lib.StorageTestCase):
    """Tests for the SQLite-based storage reader."""

    def testInitialization(self):
        """Tests the __init__ function."""
        test_path = self._GetTestFilePath(["pinfo_test.plaso"])
        test_reader = reader.SQLiteStorageReader(test_path)
        self.assertIsNotNone(test_reader)

    def testPrefetchAttributeContainers(self):
        """Tests the PrefetchAttributeContainers function."""
        test_path = self._GetTestFilePath(["pinfo_test.plaso"])
        test_identifier = containers_interface.AttributeContainerIdentifier(
            name=events.EventData.CONTAINER_TYPE, sequence_number=1
        )

        test_reader = reader.SQLiteStorageReader(test_path)

        try:
            expected_container = test_reader.GetAttributeContainerByIdentifier(
                events.EventData.CONTAINER_TYPE, test_identifier
            )
            self.assertIsNotNone(expected_container)

        finally:
            test_reader.Close()

        test_reader = reader.SQLiteStorageReader(test_path)

        try:
            test_reader.PrefetchAttributeContainers(
                events.EventData.CONTAINER_TYPE, [test_identifier]
            )

            container = test_reader.GetAttributeContainerByIdentifier(
                events.EventData.CONTAINER_TYPE, test_identifier
            )
            self.assertIsNotNone(container)
            identifier = container.GetIdentifier()
            self.assertEqual(identifier.CopyToString(), test_identifier.CopyToString())
            self.assertEqual(container.CopyToDict(), expected_container.CopyToDict())

        finally:
            test_reader.Close()


if __name__ == "__main__":
    unittest.main()
