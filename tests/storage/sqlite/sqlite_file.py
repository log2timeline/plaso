#!/usr/bin/env python3
"""Tests for the SQLite-based storage."""

import csv
import gzip
import json
import os
import sqlite3
import unittest
import zlib

from acstore.containers import interface as containers_interface

from plaso.containers import events
from plaso.engine import configurations
from plaso.engine import profilers
from plaso.lib import definitions
from plaso.storage import time_range as storage_time_range
from plaso.storage.sqlite import sqlite_file

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class _TestSQLiteStorageFileV20220716(sqlite_file.SQLiteStorageFile):
    """Test class for testing format compatibility checks."""

    _FORMAT_VERSION = 20220716
    _APPEND_COMPATIBLE_FORMAT_VERSION = 20211121
    _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20211121
    _READ_COMPATIBLE_FORMAT_VERSION = 20211121


class _TestSQLiteStorageFileV20221023(sqlite_file.SQLiteStorageFile):
    """Test class for testing format compatibility checks."""

    _FORMAT_VERSION = 20221023
    _APPEND_COMPATIBLE_FORMAT_VERSION = 20221023
    _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20221023
    _READ_COMPATIBLE_FORMAT_VERSION = 20211121


class _TestSQLiteStorageFileWithoutInMemorySize(sqlite_file.SQLiteStorageFile):
    """Test class for testing moving an in-memory database to file."""

    _MAXIMUM_IN_MEMORY_SIZE = 0


class _TestSQLiteStorageFileV20221023Upgrade(sqlite_file.SQLiteStorageFile):
    """Test class for testing format version upgrades."""

    _FORMAT_VERSION = 20221023
    _APPEND_COMPATIBLE_FORMAT_VERSION = 20220716
    _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20220716
    _READ_COMPATIBLE_FORMAT_VERSION = 20211121


class SQLiteStorageFileTest(test_lib.StorageTestCase):
    """Tests for the SQLite-based storage file object."""

    # pylint: disable=protected-access

    def testInitialization(self):
        """Tests the __init__ function."""
        test_store = sqlite_file.SQLiteStorageFile()
        self.assertIsNotNone(test_store)

    def testCacheAttributeContainerByIndex(self):
        """Tests the _CacheAttributeContainerByIndex function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory():
            test_store = sqlite_file.SQLiteStorageFile()

            self.assertEqual(len(test_store._attribute_container_cache), 0)

            test_store._CacheAttributeContainerByIndex(event_data_stream, 0)
            self.assertEqual(len(test_store._attribute_container_cache), 1)

    def testCheckStorageMetadata(self):
        """Tests the _CheckStorageMetadata function."""
        with shared_test_lib.TempDirectory():
            test_store = sqlite_file.SQLiteStorageFile()

            metadata_values = {
                "compression_format": definitions.COMPRESSION_FORMAT_ZLIB,
                "format_version": f"{test_store._FORMAT_VERSION:d}",
                "serialization_format": definitions.SERIALIZER_FORMAT_JSON,
            }
            test_store._CheckStorageMetadata(metadata_values)

            metadata_values["format_version"] = "bogus"
            with self.assertRaises(OSError):
                test_store._CheckStorageMetadata(metadata_values)

            metadata_values["format_version"] = "1"
            with self.assertRaises(OSError):
                test_store._CheckStorageMetadata(metadata_values)

            metadata_values["format_version"] = f"{test_store._FORMAT_VERSION:d}"
            metadata_values["compression_format"] = None
            with self.assertRaises(OSError):
                test_store._CheckStorageMetadata(metadata_values)

            metadata_values["compression_format"] = definitions.COMPRESSION_FORMAT_ZLIB
            metadata_values["serialization_format"] = None
            with self.assertRaises(OSError):
                test_store._CheckStorageMetadata(metadata_values)

            metadata_values["serialization_format"] = definitions.SERIALIZER_FORMAT_JSON
            with self.assertRaises(OSError):
                test_store._CheckStorageMetadata(metadata_values)

    def testCreateAttributeContainerTable(self):
        """Tests the _CreateAttributeContainerTable function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store._CreateAttributeContainerTable(
                    event_data_stream.CONTAINER_TYPE
                )

                with self.assertRaises(OSError):
                    test_store._CreateAttributeContainerTable(
                        event_data_stream.CONTAINER_TYPE
                    )

            finally:
                test_store.Close()

    def testCreateAttributeContainerFromRow(self):
        """Tests the _CreateAttributeContainerFromRow function."""
        event_data = events.EventData(data_type="test:event")

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store.AddAttributeContainer(event_data)
                test_store._CommitWriteCache(event_data.CONTAINER_TYPE)

                test_store._cursor.execute(
                    f"SELECT _data FROM {event_data.CONTAINER_TYPE:s} WHERE rowid = 1"
                )
                row = test_store._cursor.fetchone()

                container = test_store._CreateAttributeContainerFromRow(
                    event_data.CONTAINER_TYPE, ["_data"], row, 0
                )
                self.assertIsNotNone(container)
                self.assertEqual(container.CONTAINER_TYPE, event_data.CONTAINER_TYPE)
                self.assertEqual(container.data_type, "test:event")

                # Data that is not compressed.
                test_store.compression_format = definitions.COMPRESSION_FORMAT_NONE
                serialized_data = test_store._SerializeAttributeContainer(event_data)

                container = test_store._CreateAttributeContainerFromRow(
                    event_data.CONTAINER_TYPE, ["_data"], [serialized_data], 0
                )
                self.assertIsNotNone(container)
                self.assertEqual(container.data_type, "test:event")

                # Compressed data read as if it was not compressed.
                compressed_data = zlib.compress(serialized_data)
                with self.assertRaises(OSError):
                    test_store._CreateAttributeContainerFromRow(
                        event_data.CONTAINER_TYPE, ["_data"], [compressed_data], 0
                    )

            finally:
                test_store.compression_format = definitions.COMPRESSION_FORMAT_ZLIB
                test_store.Close()

    def testDeserializeAttributeContainer(self):
        """Tests the _DeserializeAttributeContainer function."""
        event_data_stream_identifier = (
            containers_interface.AttributeContainerIdentifier(
                name=events.EventDataStream.CONTAINER_TYPE, sequence_number=5
            )
        )

        event_data = events.EventData(data_type="test:event")
        event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)

        test_store = sqlite_file.SQLiteStorageFile()

        serialized_data = test_store._SerializeAttributeContainer(event_data)

        container = test_store._DeserializeAttributeContainer(
            event_data.CONTAINER_TYPE, serialized_data
        )
        self.assertIsNotNone(container)
        self.assertEqual(container.data_type, "test:event")

        identifier = container.GetEventDataStreamIdentifier()
        self.assertIsNotNone(identifier)
        self.assertEqual(
            identifier.CopyToString(), event_data_stream_identifier.CopyToString()
        )

        container = test_store._DeserializeAttributeContainer(
            event_data.CONTAINER_TYPE, b""
        )
        self.assertIsNone(container)

        with self.assertRaises(OSError):
            test_store._DeserializeAttributeContainer(
                event_data.CONTAINER_TYPE, b"\xff\xfe"
            )

        with self.assertRaises(OSError):
            test_store._DeserializeAttributeContainer(
                event_data.CONTAINER_TYPE, b"{bogus"
            )

    def testGetAttributeContainersWithFilter(self):
        """Tests the _GetAttributeContainersWithFilter function."""
        event_data_stream = events.EventDataStream()
        event_data_stream.md5_hash = "8f0bf95a7959baad9666b21a7feed79d"

        column_names = ["md5_hash"]

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                containers = list(
                    test_store._GetAttributeContainersWithFilter(
                        event_data_stream.CONTAINER_TYPE, column_names=column_names
                    )
                )
                self.assertEqual(len(containers), 0)

                test_store.AddAttributeContainer(event_data_stream)

                containers = list(
                    test_store._GetAttributeContainersWithFilter(
                        event_data_stream.CONTAINER_TYPE, column_names=column_names
                    )
                )
                self.assertEqual(len(containers), 1)

                filter_expression = 'md5_hash == "8f0bf95a7959baad9666b21a7feed79d"'
                containers = list(
                    test_store._GetAttributeContainersWithFilter(
                        event_data_stream.CONTAINER_TYPE,
                        column_names=column_names,
                        filter_expression=filter_expression,
                    )
                )
                self.assertEqual(len(containers), 1)

                filter_expression = 'md5_hash != "8f0bf95a7959baad9666b21a7feed79d"'
                containers = list(
                    test_store._GetAttributeContainersWithFilter(
                        event_data_stream.CONTAINER_TYPE,
                        column_names=column_names,
                        filter_expression=filter_expression,
                    )
                )
                self.assertEqual(len(containers), 0)

                containers = list(
                    test_store._GetAttributeContainersWithFilter(
                        "bogus", column_names=column_names
                    )
                )
                self.assertEqual(len(containers), 0)

            finally:
                test_store.Close()

    def testGetCachedAttributeContainer(self):
        """Tests the _GetCachedAttributeContainer function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory():
            test_store = sqlite_file.SQLiteStorageFile()

            attribute_container = test_store._GetCachedAttributeContainer(
                event_data_stream.CONTAINER_TYPE, 1
            )
            self.assertIsNone(attribute_container)

            test_store._CacheAttributeContainerByIndex(event_data_stream, 1)

            attribute_container = test_store._GetCachedAttributeContainer(
                event_data_stream.CONTAINER_TYPE, 1
            )
            self.assertIsNotNone(attribute_container)

    def testHasTable(self):
        """Tests the _HasTable function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store._CreateAttributeContainerTable(
                    events.EventDataStream.CONTAINER_TYPE
                )

                result = test_store._HasTable(events.EventDataStream.CONTAINER_TYPE)
                self.assertTrue(result)

                result = test_store._HasTable("bogus")
                self.assertFalse(result)

            finally:
                test_store.Close()

    def testRaiseIfNotReadable(self):
        """Tests the _RaiseIfNotReadable function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()

            with self.assertRaises(OSError):
                test_store._RaiseIfNotReadable()

            test_store.Open(path=test_path, read_only=False)
            test_store.Close()

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path)

            try:
                test_store._RaiseIfNotReadable()
            finally:
                test_store.Close()

            with self.assertRaises(OSError):
                test_store._RaiseIfNotReadable()

    def testRaiseIfNotWritable(self):
        """Tests the _RaiseIfNotWritable function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()

            with self.assertRaises(OSError):
                test_store._RaiseIfNotWritable()

            test_store.Open(path=test_path, read_only=False)

            try:
                test_store._RaiseIfNotWritable()
            finally:
                test_store.Close()

            with self.assertRaises(OSError):
                test_store._RaiseIfNotWritable()

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path)

            try:
                with self.assertRaises(OSError):
                    test_store._RaiseIfNotWritable()
            finally:
                test_store.Close()

    def testReadAndCheckStorageMetadata(self):
        """Tests the _ReadAndCheckStorageMetadata function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store.format_version = None
                test_store.compression_format = None
                test_store.serialization_format = None

                test_store._ReadAndCheckStorageMetadata()

                self.assertEqual(test_store.format_version, test_store._FORMAT_VERSION)
                self.assertEqual(
                    test_store.compression_format, definitions.COMPRESSION_FORMAT_ZLIB
                )
                self.assertEqual(
                    test_store.serialization_format, definitions.SERIALIZER_FORMAT_JSON
                )

                test_store._cursor.execute(
                    'UPDATE metadata SET value = "bogus" '
                    'WHERE key = "compression_format"'
                )

                with self.assertRaises(OSError):
                    test_store._ReadAndCheckStorageMetadata()

            finally:
                test_store.Close()

    def testSerializeAttributeContainer(self):
        """Tests the _SerializeAttributeContainer function."""
        event_data_stream_identifier = (
            containers_interface.AttributeContainerIdentifier(
                name=events.EventDataStream.CONTAINER_TYPE, sequence_number=5
            )
        )

        event_data = events.EventData(data_type="test:event")

        test_store = sqlite_file.SQLiteStorageFile()

        serialized_data = test_store._SerializeAttributeContainer(event_data)
        self.assertIsInstance(serialized_data, bytes)

        json_dict = json.loads(serialized_data.decode("utf-8"))
        self.assertEqual(json_dict["__container_type__"], event_data.CONTAINER_TYPE)
        self.assertEqual(json_dict["data_type"], "test:event")
        self.assertNotIn("_event_data_stream_identifier", json_dict)

        event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)

        serialized_data = test_store._SerializeAttributeContainer(event_data)

        json_dict = json.loads(serialized_data.decode("utf-8"))
        self.assertEqual(
            json_dict["_event_data_stream_identifier"],
            event_data_stream_identifier.CopyToString(),
        )

        # An attribute value that cannot be serialized to JSON.
        event_data.unsupported = object()

        with self.assertRaises(OSError):
            test_store._SerializeAttributeContainer(event_data)

    def testUpdateStorageMetadataFormatVersion(self):
        """Tests the _UpdateStorageMetadataFormatVersion function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "v20220716.sqlite")
            test_store = _TestSQLiteStorageFileV20220716()
            test_store.Open(path=test_path, read_only=False)
            test_store.Close()

            # Opening the store for writing upgrades the format version.
            test_store = _TestSQLiteStorageFileV20221023Upgrade()
            test_store.Open(path=test_path, read_only=False)

            try:
                metadata_values = test_store._ReadMetadata()
                self.assertEqual(metadata_values["format_version"], "20221023")

                # The stored format version is not updated when the format version
                # of the store is not upgrade compatible.
                test_store._cursor.execute(
                    'UPDATE metadata SET value = "20220716" '
                    'WHERE key = "format_version"'
                )

                test_store.format_version = 20211121
                test_store._UpdateStorageMetadataFormatVersion()

                metadata_values = test_store._ReadMetadata()
                self.assertEqual(metadata_values["format_version"], "20220716")

                test_store.format_version = 20220716
                test_store._UpdateStorageMetadataFormatVersion()

                metadata_values = test_store._ReadMetadata()
                self.assertEqual(metadata_values["format_version"], "20221023")

            finally:
                test_store.Close()

    def testWriteExistingAttributeContainer(self):
        """Tests the _WriteExistingAttributeContainer function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                number_of_containers = test_store._GetNumberOfAttributeContainerRows(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 0)

                test_store._WriteNewAttributeContainer(event_data_stream)

                number_of_containers = test_store._GetNumberOfAttributeContainerRows(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 1)

                test_store._WriteExistingAttributeContainer(event_data_stream)

                number_of_containers = test_store._GetNumberOfAttributeContainerRows(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 1)

            finally:
                test_store.Close()

    def testWriteMetadata(self):
        """Tests the _WriteMetadata function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store._cursor.execute("DROP TABLE metadata")

                test_store.compression_format = definitions.COMPRESSION_FORMAT_NONE
                test_store._WriteMetadata()

                metadata_values = test_store._ReadMetadata()
                self.assertEqual(
                    metadata_values,
                    {
                        "compression_format": definitions.COMPRESSION_FORMAT_NONE,
                        "format_version": f"{test_store._FORMAT_VERSION:d}",
                        "serialization_format": definitions.SERIALIZER_FORMAT_JSON,
                    },
                )

                # The metadata table already exists.
                with self.assertRaises(OSError):
                    test_store._WriteMetadata()

            finally:
                test_store.Close()

    def testWriteMetadataValue(self):
        """Tests the _WriteMetadataValue function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                metadata_values = test_store._ReadMetadata()
                self.assertNotIn("test_key", metadata_values)

                test_store._WriteMetadataValue("test_key", "test_value")

                metadata_values = test_store._ReadMetadata()
                self.assertEqual(metadata_values.get("test_key"), "test_value")

                test_store._cursor.execute("DROP TABLE metadata")

                with self.assertRaises(OSError):
                    test_store._WriteMetadataValue("test_key", "test_value")

            finally:
                test_store.Close()

    def testWriteNewAttributeContainer(self):
        """Tests the _WriteNewAttributeContainer function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                number_of_containers = test_store._GetNumberOfAttributeContainerRows(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 0)

                test_store._WriteNewAttributeContainer(event_data_stream)

                number_of_containers = test_store._GetNumberOfAttributeContainerRows(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 1)

            finally:
                test_store.Close()

    def testWriteNewAttributeContainerWithStorageProfiler(self):
        """Tests the _WriteNewAttributeContainer function with a storage profiler."""
        event_data = events.EventData()
        event_data.data_type = "test:event_data"
        event_data.body = "test" * 256

        profiling_configuration = configurations.ProfilingConfiguration()

        with shared_test_lib.TempDirectory() as temp_directory:
            profiling_configuration.directory = temp_directory

            test_profiler = profilers.StorageProfiler("test", profiling_configuration)
            test_profiler.Start()

            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.SetStorageProfiler(test_profiler)
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store._WriteNewAttributeContainer(event_data)
            finally:
                test_store.Close()
                test_profiler.Stop()

            sample_path = os.path.join(temp_directory, "storage-test.csv.gz")
            with gzip.open(sample_path, "rt", encoding="utf-8") as file_object:
                rows = list(csv.reader(file_object, delimiter="\t"))

        write_rows = [row for row in rows if row[1] == "write_new"]
        self.assertEqual(len(write_rows), 1)

        data_size = int(write_rows[0][5])
        compressed_data_size = int(write_rows[0][6])

        self.assertGreater(data_size, compressed_data_size)

    def testAddAttributeContainer(self):
        """Tests the AddAttributeContainer function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 0)

                test_store.AddAttributeContainer(event_data_stream)

                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 1)

            finally:
                test_store.Close()

            with self.assertRaises(OSError):
                test_store.AddAttributeContainer(event_data_stream)

    def testCheckSupportedFormat(self):
        """Tests the CheckSupportedFormat function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")

            result = sqlite_file.SQLiteStorageFile.CheckSupportedFormat(test_path)
            self.assertFalse(result)
            self.assertFalse(os.path.exists(test_path))

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)
            test_store.Close()

            result = sqlite_file.SQLiteStorageFile.CheckSupportedFormat(test_path)
            self.assertTrue(result)

            test_path = os.path.join(temp_directory, "bogus.sqlite")
            with open(test_path, "wb") as file_object:
                file_object.write(b"bogus")

            result = sqlite_file.SQLiteStorageFile.CheckSupportedFormat(test_path)
            self.assertFalse(result)

            # A SQLite database without a metadata table.
            test_path = os.path.join(temp_directory, "other.sqlite")
            connection = sqlite3.connect(test_path)
            connection.execute("CREATE TABLE other (value TEXT)")
            connection.commit()
            connection.close()

            result = sqlite_file.SQLiteStorageFile.CheckSupportedFormat(test_path)
            self.assertFalse(result)

    def testGetAttributeContainers(self):
        """Tests the GetAttributeContainers function."""
        event_data_stream = events.EventDataStream()
        event_data_stream.md5_hash = "8f0bf95a7959baad9666b21a7feed79d"

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                containers = list(
                    test_store.GetAttributeContainers(event_data_stream.CONTAINER_TYPE)
                )
                self.assertEqual(len(containers), 0)

                test_store.AddAttributeContainer(event_data_stream)

                containers = list(
                    test_store.GetAttributeContainers(event_data_stream.CONTAINER_TYPE)
                )
                self.assertEqual(len(containers), 1)

                filter_expression = 'md5_hash == "8f0bf95a7959baad9666b21a7feed79d"'
                containers = list(
                    test_store.GetAttributeContainers(
                        event_data_stream.CONTAINER_TYPE,
                        filter_expression=filter_expression,
                    )
                )
                self.assertEqual(len(containers), 1)

                filter_expression = 'md5_hash != "8f0bf95a7959baad9666b21a7feed79d"'
                containers = list(
                    test_store.GetAttributeContainers(
                        event_data_stream.CONTAINER_TYPE,
                        filter_expression=filter_expression,
                    )
                )
                self.assertEqual(len(containers), 0)

                containers = list(test_store.GetAttributeContainers("bogus"))
                self.assertEqual(len(containers), 0)

            finally:
                test_store.Close()

    def testGetAttributeContainerByIdentifier(self):
        """Tests the GetAttributeContainerByIdentifier function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store.AddAttributeContainer(event_data_stream)

                identifier = event_data_stream.GetIdentifier()

                container = test_store.GetAttributeContainerByIdentifier(
                    event_data_stream.CONTAINER_TYPE, identifier
                )
                self.assertIsNotNone(container)

                identifier.sequence_number = 99

                container = test_store.GetAttributeContainerByIdentifier(
                    event_data_stream.CONTAINER_TYPE, identifier
                )
                self.assertIsNone(container)

            finally:
                test_store.Close()

    def testGetAttributeContainerByIndex(self):
        """Tests the GetAttributeContainerByIndex function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                container = test_store.GetAttributeContainerByIndex(
                    event_data_stream.CONTAINER_TYPE, 0
                )
                self.assertIsNone(container)

                test_store.AddAttributeContainer(event_data_stream)

                container = test_store.GetAttributeContainerByIndex(
                    event_data_stream.CONTAINER_TYPE, 0
                )
                self.assertIsNotNone(container)

                container = test_store.GetAttributeContainerByIndex("bogus", 0)
                self.assertIsNone(container)

            finally:
                test_store.Close()

    def testGetAttributeContainerByIndexWithEventData(self):
        """Tests the GetAttributeContainerByIndex function with event data."""
        event_data = events.EventData(data_type="test:event")
        event_data._corrupted = True
        event_data._recovered = True

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                test_store.AddAttributeContainer(event_data)
            finally:
                test_store.Close()

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path)

            try:
                container = test_store.GetAttributeContainerByIndex(
                    event_data.CONTAINER_TYPE, 0
                )
                self.assertIsNotNone(container)
                self.assertTrue(container._corrupted)
                self.assertTrue(container._recovered)

            finally:
                test_store.Close()

    def testGetNumberOfAttributeContainers(self):
        """Tests the GetNumberOfAttributeContainers function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 0)

                test_store.AddAttributeContainer(event_data_stream)

                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 1)

                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    "bogus"
                )
                self.assertEqual(number_of_containers, 0)

            finally:
                test_store.Close()

    def testMoveInMemoryDatabaseToFile(self):
        """Tests the _MoveInMemoryDatabaseToFile function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = _TestSQLiteStorageFileWithoutInMemorySize()
            test_store.Open(path=test_path, read_only=False, in_memory=True)

            try:
                self.assertFalse(os.path.exists(test_path))

                for md5_hash in ("8f0bf95a7959baad9666b21a7feed79d", None):
                    event_data_stream = events.EventDataStream()
                    event_data_stream.md5_hash = md5_hash
                    test_store.AddAttributeContainer(event_data_stream)

                # The in-memory database exceeds the maximum in-memory size when
                # the cached attribute containers are written.
                test_store._Flush()

                self.assertIsNone(test_store._in_memory_path)
                self.assertTrue(os.path.exists(test_path))

                event_data_stream = events.EventDataStream()
                test_store.AddAttributeContainer(event_data_stream)

            finally:
                test_store.Close()

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=True)

            try:
                containers = list(
                    test_store.GetAttributeContainers(event_data_stream.CONTAINER_TYPE)
                )
                self.assertEqual(len(containers), 3)
                self.assertEqual(
                    containers[0].md5_hash, "8f0bf95a7959baad9666b21a7feed79d"
                )

            finally:
                test_store.Close()

            # The in-memory database exceeds the maximum in-memory size when the
            # cached attribute containers are written on close.
            test_path = os.path.join(temp_directory, "plaso2.sqlite")
            test_store = _TestSQLiteStorageFileWithoutInMemorySize()
            test_store.Open(path=test_path, read_only=False, in_memory=True)

            try:
                for _ in range(2):
                    test_store.AddAttributeContainer(events.EventDataStream())

            finally:
                test_store.Close()

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=True)

            try:
                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 2)

            finally:
                test_store.Close()

    def testGetSortedEvents(self):
        """Tests the GetSortedEvents function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                for (
                    event,
                    event_data,
                    event_data_stream,
                ) in containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS):
                    test_store.AddAttributeContainer(event_data_stream)

                    event_data.SetEventDataStreamIdentifier(
                        event_data_stream.GetIdentifier()
                    )
                    test_store.AddAttributeContainer(event_data)

                    event.SetEventDataIdentifier(event_data.GetIdentifier())
                    test_store.AddAttributeContainer(event)

            finally:
                test_store.Close()

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path)

            try:
                test_events = list(test_store.GetSortedEvents())
                self.assertEqual(len(test_events), 4)

                time_range = storage_time_range.TimeRange(
                    1334940286000000, 1334961526929596
                )
                test_events = list(test_store.GetSortedEvents(time_range=time_range))
                timestamps = [event.timestamp for event in test_events]
                self.assertEqual(timestamps, [1334940286000000, 1334961526929596])

            finally:
                test_store.Close()

    def testHasAttributeContainers(self):
        """Tests the HasAttributeContainers function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                result = test_store.HasAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertFalse(result)

                test_store.AddAttributeContainer(event_data_stream)

                result = test_store.HasAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertTrue(result)

                result = test_store.HasAttributeContainers("bogus")
                self.assertFalse(result)

            finally:
                test_store.Close()

    # TODO: add tests for Open and Close

    def testUpdateAttributeContainer(self):
        """Tests the UpdateAttributeContainer function."""
        event_data_stream = events.EventDataStream()

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False)

            try:
                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 0)

                test_store.AddAttributeContainer(event_data_stream)

                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 1)

                test_store.UpdateAttributeContainer(event_data_stream)

                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 1)

            finally:
                test_store.Close()

    def testOpenCloseInMemory(self):
        """Tests the Open and Close functions with an in-memory database."""
        event_data_stream = events.EventDataStream()
        event_data_stream.md5_hash = "8f0bf95a7959baad9666b21a7feed79d"

        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "plaso.sqlite")
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False, in_memory=True)

            try:
                test_store.AddAttributeContainer(event_data_stream)

                event_data_stream.sha256_hash = (
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                )
                test_store.UpdateAttributeContainer(event_data_stream)

                # The in-memory database is only written to the storage file on
                # close.
                self.assertFalse(os.path.exists(test_path))

            finally:
                test_store.Close()

            self.assertTrue(os.path.exists(test_path))

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=True)

            try:
                containers = list(
                    test_store.GetAttributeContainers(event_data_stream.CONTAINER_TYPE)
                )
                self.assertEqual(len(containers), 1)
                self.assertEqual(
                    containers[0].md5_hash, "8f0bf95a7959baad9666b21a7feed79d"
                )
                self.assertEqual(
                    containers[0].sha256_hash,
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                )

            finally:
                test_store.Close()

            # An existing storage file is opened instead of an in-memory database.
            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=False, in_memory=True)

            try:
                self.assertIsNone(test_store._in_memory_path)

                test_store.AddAttributeContainer(events.EventDataStream())

            finally:
                test_store.Close()

            test_store = sqlite_file.SQLiteStorageFile()
            test_store.Open(path=test_path, read_only=True)

            try:
                number_of_containers = test_store.GetNumberOfAttributeContainers(
                    event_data_stream.CONTAINER_TYPE
                )
                self.assertEqual(number_of_containers, 2)

            finally:
                test_store.Close()

    def testVersionCompatibility(self):
        """Tests the version compatibility methods."""
        with shared_test_lib.TempDirectory() as temp_directory:
            v1_storage_path = os.path.join(temp_directory, "v20220716.sqlite")
            v1_test_store = _TestSQLiteStorageFileV20220716()
            v1_test_store.Open(path=v1_storage_path, read_only=False)
            v1_test_store.Close()

            v2_test_store_rw = _TestSQLiteStorageFileV20221023()

            with self.assertRaises(OSError):
                v2_test_store_rw.Open(path=v1_storage_path, read_only=False)

            v2_test_store_ro = _TestSQLiteStorageFileV20221023()
            v2_test_store_ro.Open(path=v1_storage_path, read_only=True)
            v2_test_store_ro.Close()


if __name__ == "__main__":
    unittest.main()
