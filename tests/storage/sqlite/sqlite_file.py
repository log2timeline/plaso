#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite-based storage."""

import os
import unittest

from plaso.containers import events
from plaso.lib import definitions
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
          'compression_format': definitions.COMPRESSION_FORMAT_ZLIB,
          'format_version': '{0:d}'.format(test_store._FORMAT_VERSION),
          'serialization_format': definitions.SERIALIZER_FORMAT_JSON}
      test_store._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = 'bogus'
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = '1'
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = '{0:d}'.format(
          test_store._FORMAT_VERSION)
      metadata_values['compression_format'] = None
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['compression_format'] = (
          definitions.COMPRESSION_FORMAT_ZLIB)
      metadata_values['serialization_format'] = None
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

      metadata_values['serialization_format'] = (
          definitions.SERIALIZER_FORMAT_JSON)
      with self.assertRaises(IOError):
        test_store._CheckStorageMetadata(metadata_values)

  def testCreateAttributeContainerTable(self):
    """Tests the _CreateAttributeContainerTable function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        test_store._CreateAttributeContainerTable(
            event_data_stream.CONTAINER_TYPE)

        with self.assertRaises(IOError):
          test_store._CreateAttributeContainerTable(
              event_data_stream.CONTAINER_TYPE)

      finally:
        test_store.Close()

  # TODO: add tests for _CreateAttributeContainerFromRow
  # TODO: add tests for _DeserializeAttributeContainer

  def testGetAttributeContainersWithFilter(self):
    """Tests the _GetAttributeContainersWithFilter function."""
    event_data_stream = events.EventDataStream()
    event_data_stream.md5_hash = '8f0bf95a7959baad9666b21a7feed79d'

    column_names = ['md5_hash']

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        containers = list(test_store._GetAttributeContainersWithFilter(
            event_data_stream.CONTAINER_TYPE, column_names=column_names))
        self.assertEqual(len(containers), 0)

        test_store.AddAttributeContainer(event_data_stream)

        containers = list(test_store._GetAttributeContainersWithFilter(
            event_data_stream.CONTAINER_TYPE, column_names=column_names))
        self.assertEqual(len(containers), 1)

        filter_expression = 'md5_hash == "8f0bf95a7959baad9666b21a7feed79d"'
        containers = list(test_store._GetAttributeContainersWithFilter(
            event_data_stream.CONTAINER_TYPE, column_names=column_names,
            filter_expression=filter_expression))
        self.assertEqual(len(containers), 1)

        filter_expression = 'md5_hash != "8f0bf95a7959baad9666b21a7feed79d"'
        containers = list(test_store._GetAttributeContainersWithFilter(
            event_data_stream.CONTAINER_TYPE, column_names=column_names,
            filter_expression=filter_expression))
        self.assertEqual(len(containers), 0)

        containers = list(test_store._GetAttributeContainersWithFilter(
            'bogus', column_names=column_names))
        self.assertEqual(len(containers), 0)

      finally:
        test_store.Close()

  def testGetCachedAttributeContainer(self):
    """Tests the _GetCachedAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory():
      test_store = sqlite_file.SQLiteStorageFile()

      attribute_container = test_store._GetCachedAttributeContainer(
          event_data_stream.CONTAINER_TYPE, 1)
      self.assertIsNone(attribute_container)

      test_store._CacheAttributeContainerByIndex(event_data_stream, 1)

      attribute_container = test_store._GetCachedAttributeContainer(
          event_data_stream.CONTAINER_TYPE, 1)
      self.assertIsNotNone(attribute_container)

  def testHasTable(self):
    """Tests the _HasTable function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        test_store._CreateAttributeContainerTable(
            events.EventDataStream.CONTAINER_TYPE)

        result = test_store._HasTable(
            events.EventDataStream.CONTAINER_TYPE)
        self.assertTrue(result)

        result = test_store._HasTable('bogus')
        self.assertFalse(result)

      finally:
        test_store.Close()

  # TODO: add tests for _RaiseIfNotReadable
  # TODO: add tests for _RaiseIfNotWritable
  # TODO: add tests for _ReadAndCheckStorageMetadata
  # TODO: add tests for _SerializeAttributeContainer
  # TODO: add tests for _UpdateEventAfterDeserialize
  # TODO: add tests for _UpdateEventBeforeSerialize
  # TODO: add tests for _UpdateEventDataAfterDeserialize
  # TODO: add tests for _UpdateEventDataBeforeSerialize
  # TODO: add tests for _UpdateEventTagAfterDeserialize
  # TODO: add tests for _UpdateEventTagBeforeSerialize
  # TODO: add tests for _UpdateStorageMetadataFormatVersion

  def testWriteExistingAttributeContainer(self):
    """Tests the _WriteExistingAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 0)

        test_store._WriteNewAttributeContainer(event_data_stream)

        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 1)

        test_store._WriteExistingAttributeContainer(event_data_stream)

        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 1)

      finally:
        test_store.Close()

  # TODO: add tests for _WriteMetadata
  # TODO: add tests for _WriteMetadataValue

  def testWriteNewAttributeContainer(self):
    """Tests the _WriteNewAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 0)

        test_store._WriteNewAttributeContainer(event_data_stream)

        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 1)

      finally:
        test_store.Close()

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 0)

        test_store.AddAttributeContainer(event_data_stream)

        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 1)

      finally:
        test_store.Close()

      with self.assertRaises(IOError):
        test_store.AddAttributeContainer(event_data_stream)

  # TODO: add tests for CheckSupportedFormat

  def testGetAttributeContainers(self):
    """Tests the GetAttributeContainers function."""
    event_data_stream = events.EventDataStream()
    event_data_stream.md5_hash = '8f0bf95a7959baad9666b21a7feed79d'

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        containers = list(test_store.GetAttributeContainers(
            event_data_stream.CONTAINER_TYPE))
        self.assertEqual(len(containers), 0)

        test_store.AddAttributeContainer(event_data_stream)

        containers = list(test_store.GetAttributeContainers(
            event_data_stream.CONTAINER_TYPE))
        self.assertEqual(len(containers), 1)

        filter_expression = 'md5_hash == "8f0bf95a7959baad9666b21a7feed79d"'
        containers = list(test_store.GetAttributeContainers(
            event_data_stream.CONTAINER_TYPE,
            filter_expression=filter_expression))
        self.assertEqual(len(containers), 1)

        filter_expression = 'md5_hash != "8f0bf95a7959baad9666b21a7feed79d"'
        containers = list(test_store.GetAttributeContainers(
            event_data_stream.CONTAINER_TYPE,
            filter_expression=filter_expression))
        self.assertEqual(len(containers), 0)

        containers = list(test_store.GetAttributeContainers('bogus'))
        self.assertEqual(len(containers), 0)

      finally:
        test_store.Close()

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        test_store.AddAttributeContainer(event_data_stream)

        identifier = event_data_stream.GetIdentifier()

        container = test_store.GetAttributeContainerByIdentifier(
            event_data_stream.CONTAINER_TYPE, identifier)
        self.assertIsNotNone(container)

        identifier.sequence_number = 99

        container = test_store.GetAttributeContainerByIdentifier(
            event_data_stream.CONTAINER_TYPE, identifier)
        self.assertIsNone(container)

      finally:
        test_store.Close()

  def testGetAttributeContainerByIndex(self):
    """Tests the GetAttributeContainerByIndex function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        container = test_store.GetAttributeContainerByIndex(
            event_data_stream.CONTAINER_TYPE, 0)
        self.assertIsNone(container)

        test_store.AddAttributeContainer(event_data_stream)

        container = test_store.GetAttributeContainerByIndex(
            event_data_stream.CONTAINER_TYPE, 0)
        self.assertIsNotNone(container)

        container = test_store.GetAttributeContainerByIndex('bogus', 0)
        self.assertIsNone(container)

      finally:
        test_store.Close()

  def testGetNumberOfAttributeContainers(self):
    """Tests the GetNumberOfAttributeContainers function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 0)

        test_store.AddAttributeContainer(event_data_stream)

        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 1)

        # Test for a supported container type that does not have a table
        # present in the storage file.
        query = 'DROP TABLE {0:s}'.format(event_data_stream.CONTAINER_TYPE)
        test_store._cursor.execute(query)
        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 0)

      finally:
        test_store.Close()

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        for event, event_data, event_data_stream in (
            containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
          test_store.AddAttributeContainer(event_data_stream)

          event_data.SetEventDataStreamIdentifier(
              event_data_stream.GetIdentifier())
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

      finally:
        test_store.Close()

    # TODO: add test with time range.

  def testHasAttributeContainers(self):
    """Tests the HasAttributeContainers function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        result = test_store.HasAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertFalse(result)

        test_store.AddAttributeContainer(event_data_stream)

        result = test_store.HasAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertTrue(result)

        result = test_store.HasAttributeContainers('bogus')
        self.assertFalse(result)

      finally:
        test_store.Close()

  # TODO: add tests for Open and Close

  def testUpdateAttributeContainer(self):
    """Tests the UpdateAttributeContainer function."""
    event_data_stream = events.EventDataStream()

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(temp_directory, 'plaso.sqlite')
      test_store = sqlite_file.SQLiteStorageFile()
      test_store.Open(path=test_path, read_only=False)

      try:
        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 0)

        test_store.AddAttributeContainer(event_data_stream)

        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 1)

        test_store.UpdateAttributeContainer(event_data_stream)

        number_of_containers = test_store.GetNumberOfAttributeContainers(
            event_data_stream.CONTAINER_TYPE)
        self.assertEqual(number_of_containers, 1)

      finally:
        test_store.Close()

  def testVersionCompatibility(self):
    """Tests the version compatibility methods."""
    with shared_test_lib.TempDirectory() as temp_directory:
      v1_storage_path = os.path.join(temp_directory, 'v20220716.sqlite')
      v1_test_store = _TestSQLiteStorageFileV20220716()
      v1_test_store.Open(path=v1_storage_path, read_only=False)
      v1_test_store.Close()

      v2_test_store_rw = _TestSQLiteStorageFileV20221023()

      with self.assertRaises((IOError, OSError)):
        v2_test_store_rw.Open(path=v1_storage_path, read_only=False)

      v2_test_store_ro = _TestSQLiteStorageFileV20221023()
      v2_test_store_ro.Open(path=v1_storage_path, read_only=True)
      v2_test_store_ro.Close()


if __name__ == '__main__':
  unittest.main()
