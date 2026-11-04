#!/usr/bin/env python3
"""Tests for the SQLite-based storage reader."""

import unittest

from plaso.lib import definitions
from plaso.storage.sqlite import reader

from tests.storage import test_lib


class SQLiteStorageReaderTest(test_lib.StorageTestCase):
    """Tests for the SQLite-based storage reader."""

    def testInitialization(self):
        """Tests the __init__ function."""
        test_path = self._GetTestFilePath(["pinfo_test.plaso"])
        test_reader = reader.SQLiteStorageReader(test_path)
        self.assertIsNotNone(test_reader)

    def testGetAttributeContainersWithStoredData(self):
        """Tests the GetAttributeContainersWithStoredData function."""
        test_path = self._GetTestFilePath(["psort_test.plaso"])
        with reader.SQLiteStorageReader(test_path) as test_reader:
            test_containers = list(
                test_reader.GetAttributeContainersWithStoredData("event_data")
            )
            self.assertEqual(len(test_containers), 34)

            # The test file stores the event data stream identifier in the
            # serialized event data, which therefore cannot be copied as-is.
            container, stored_data = test_containers[0]
            self.assertIsNone(stored_data)

            identifier = container.GetEventDataStreamIdentifier()
            self.assertEqual(identifier.CopyToString(), "event_data_stream.1")

    def testGetCompressionFormat(self):
        """Tests the GetCompressionFormat function."""
        test_path = self._GetTestFilePath(["pinfo_test.plaso"])
        with reader.SQLiteStorageReader(test_path) as test_reader:
            compression_format = test_reader.GetCompressionFormat()
            self.assertEqual(compression_format, definitions.COMPRESSION_FORMAT_ZLIB)


if __name__ == "__main__":
    unittest.main()
