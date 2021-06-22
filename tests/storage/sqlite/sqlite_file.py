#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite-based storage."""

import os
import unittest

from plaso.containers import events
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage.sqlite import sqlite_file

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class _TestSQLiteStorageFileV1(sqlite_file.SQLiteStorageFile):
  """Test class for testing format compatibility checks."""

  _FORMAT_VERSION = 1
  _APPEND_COMPATIBLE_FORMAT_VERSION = 1
  _READ_COMPATIBLE_FORMAT_VERSION = 1


class _TestSQLiteStorageFileV2(sqlite_file.SQLiteStorageFile):
  """Test class for testing format compatibility checks."""

  _FORMAT_VERSION = 2
  _APPEND_COMPATIBLE_FORMAT_VERSION = 2
  _READ_COMPATIBLE_FORMAT_VERSION = 1


class SQLiteStorageFileTest(test_lib.StorageTestCase):
  """Tests for the SQLite-based storage file object."""

  # pylint: disable=protected-access

  def testInitialization(self):
    """Tests the __init__ function."""
    storage_file = sqlite_file.SQLiteStorageFile()
    self.assertIsNotNone(storage_file)

  def testCacheAttributeContainerByIndex(self):
    """Tests the _CacheAttributeContainerByIndex function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory():
      storage_file = sqlite_file.SQLiteStorageFile()

      self.assertEqual(len(storage_file._attribute_container_cache), 0)

      storage_file._CacheAttributeContainerByIndex(event_data, 0)
      self.assertEqual(len(storage_file._attribute_container_cache), 1)

  def testCheckStorageMetadata(self):
    """Tests the _CheckStorageMetadata function."""
    with shared_test_lib.TempDirectory():
      storage_file = sqlite_file.SQLiteStorageFile()

      metadata_values = {
          'compression_format': definitions.COMPRESSION_FORMAT_ZLIB,
          'format_version': '{0:d}'.format(storage_file._FORMAT_VERSION),
          'serialization_format': definitions.SERIALIZER_FORMAT_JSON,
          'storage_type': definitions.STORAGE_TYPE_SESSION}
      storage_file._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = 'bogus'
      with self.assertRaises(IOError):
        storage_file._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = '1'
      with self.assertRaises(IOError):
        storage_file._CheckStorageMetadata(metadata_values)

      metadata_values['format_version'] = '{0:d}'.format(
          storage_file._FORMAT_VERSION)
      metadata_values['compression_format'] = None
      with self.assertRaises(IOError):
        storage_file._CheckStorageMetadata(metadata_values)

      metadata_values['compression_format'] = (
          definitions.COMPRESSION_FORMAT_ZLIB)
      metadata_values['serialization_format'] = None
      with self.assertRaises(IOError):
        storage_file._CheckStorageMetadata(metadata_values)

      metadata_values['serialization_format'] = (
          definitions.SERIALIZER_FORMAT_JSON)
      metadata_values['storage_type'] = None
      with self.assertRaises(IOError):
        storage_file._CheckStorageMetadata(metadata_values)

  def testCreateAttributeContainerTable(self):
    """Tests the _CreateAttributeContainerTable function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      with self.assertRaises(IOError):
        storage_file._CreateAttributeContainerTable(
            event_data.CONTAINER_TYPE)

      storage_file.Close()

  # TODO: add tests for _CreatetAttributeContainerFromRow

  def testGetAttributeContainers(self):
    """Tests the _GetAttributeContainers function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      containers = list(storage_file._GetAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA))
      self.assertEqual(len(containers), 0)

      storage_file.AddAttributeContainer(event_data)

      containers = list(storage_file._GetAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA))
      self.assertEqual(len(containers), 1)

      with self.assertRaises(IOError):
        list(storage_file._GetAttributeContainers('bogus'))

      storage_file.Close()

  def testGetCachedAttributeContainer(self):
    """Tests the _GetCachedAttributeContainer function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory():
      storage_file = sqlite_file.SQLiteStorageFile()

      attribute_container = storage_file._GetCachedAttributeContainer(
          events.EventData.CONTAINER_TYPE, 1)
      self.assertIsNone(attribute_container)

      storage_file._CacheAttributeContainerByIndex(event_data, 1)

      attribute_container = storage_file._GetCachedAttributeContainer(
          events.EventData.CONTAINER_TYPE, 1)
      self.assertIsNotNone(attribute_container)

  def testHasTable(self):
    """Tests the _HasTable function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      result = storage_file._HasTable(storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertTrue(result)

      result = storage_file._HasTable('bogus')
      self.assertFalse(result)

      storage_file.Close()

  # TODO: add tests for _ReadAndCheckStorageMetadata
  # TODO: add tests for _UpdateAttributeContainerAfterDeserialize
  # TODO: add tests for _UpdateAttributeContainerBeforeSerialize
  # TODO: add tests for _UpdateEventAfterDeserialize
  # TODO: add tests for _UpdateEventBeforeSerialize
  # TODO: add tests for _UpdateEventDataAfterDeserialize
  # TODO: add tests for _UpdateEventDataBeforeSerialize
  # TODO: add tests for _UpdateEventTagAfterDeserialize
  # TODO: add tests for _UpdateEventTagBeforeSerialize
  # TODO: add tests for _UpdateStorageMetadataFormatVersion
  # TODO: add tests for _WriteExistingAttributeContainer
  # TODO: add tests for _WriteMetadata
  # TODO: add tests for _WriteMetadataValue

  def testWriteNewAttributeContainer(self):
    """Tests the _WriteNewAttributeContainer function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file._WriteNewAttributeContainer(event_data)

      storage_file.Close()

  def testAddAttributeContainer(self):
    """Tests the AddAttributeContainer function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddAttributeContainer(event_data)

      storage_file.Close()

  # TODO: refactor
  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      test_events = []
      for event, event_data, event_data_stream in (
          containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
        storage_file.AddAttributeContainer(event_data_stream)

        event_data.SetEventDataStreamIdentifier(
            event_data_stream.GetIdentifier())
        storage_file.AddAttributeContainer(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        storage_file.AddAttributeContainer(event)

        test_events.append(event)

      test_event_tags = self._CreateTestEventTags(test_events)
      for event_tag in test_event_tags:
        storage_file.AddEventTag(event_tag)

      storage_file.Close()

  # TODO: add tests for CheckSupportedFormat

  def testGetAttributeContainerByIndex(self):
    """Tests the GetAttributeContainerByIndex function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      container = storage_file.GetAttributeContainerByIndex(
          storage_file._CONTAINER_TYPE_EVENT_DATA, 0)
      self.assertIsNone(container)

      storage_file.AddAttributeContainer(event_data)

      container = storage_file.GetAttributeContainerByIndex(
          storage_file._CONTAINER_TYPE_EVENT_DATA, 0)
      self.assertIsNotNone(container)

      with self.assertRaises(IOError):
        storage_file.GetAttributeContainerByIndex('bogus', 0)

      storage_file.Close()

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddAttributeContainer(event_data)
      identifier = event_data.GetIdentifier()

      container = storage_file.GetAttributeContainerByIdentifier(
          storage_file._CONTAINER_TYPE_EVENT_DATA, identifier)
      self.assertIsNotNone(container)

      identifier.row_identifier = 99

      container = storage_file.GetAttributeContainerByIdentifier(
          storage_file._CONTAINER_TYPE_EVENT_DATA, identifier)
      self.assertIsNone(container)

      storage_file.Close()

  def testGetNumberOfAttributeContainers(self):
    """Tests the GetNumberOfAttributeContainers function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      number_of_containers = storage_file.GetNumberOfAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertEqual(number_of_containers, 0)

      storage_file.AddAttributeContainer(event_data)

      number_of_containers = storage_file.GetNumberOfAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertEqual(number_of_containers, 1)

      with self.assertRaises(ValueError):
        storage_file.GetNumberOfAttributeContainers('bogus')

      # Test for a supported container type that does not have a table
      # present in the storage file.
      query = 'DROP TABLE {0:s}'.format(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      storage_file._cursor.execute(query)
      number_of_containers = storage_file.GetNumberOfAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertEqual(number_of_containers, 0)

      storage_file.Close()

  # TODO: add tests for GetSessions

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event, event_data, event_data_stream in (
          containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
        storage_file.AddAttributeContainer(event_data_stream)

        event_data.SetEventDataStreamIdentifier(
            event_data_stream.GetIdentifier())
        storage_file.AddAttributeContainer(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        storage_file.AddAttributeContainer(event)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_events = list(storage_file.GetSortedEvents())
      self.assertEqual(len(test_events), 4)

      storage_file.Close()

    # TODO: add test with time range.

  def testHasAttributeContainers(self):
    """Tests the HasAttributeContainers function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      result = storage_file.HasAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertFalse(result)

      storage_file.AddAttributeContainer(event_data)

      result = storage_file.HasAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertTrue(result)

      with self.assertRaises(ValueError):
        storage_file.HasAttributeContainers('bogus')

      storage_file.Close()

  # TODO: add tests for Open and Close

  # TODO: add tests for ReadSystemConfiguration

  def testWriteSessionStartConfigurationAndCompletion(self):
    """Tests the WriteSessionStart, Configuration and Completion functions."""
    session = sessions.Session()
    session_start = sessions.SessionStart(identifier=session.identifier)
    session_configuration = sessions.SessionConfiguration(
        identifier=session.identifier)
    session_completion = sessions.SessionCompletion(
        identifier=session.identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile(
          storage_type=definitions.STORAGE_TYPE_SESSION)
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.WriteSessionStart(session_start)
      storage_file.WriteSessionConfiguration(session_configuration)
      storage_file.WriteSessionCompletion(session_completion)

      storage_file.Close()

  def testWriteTaskStartAndCompletion(self):
    """Tests the WriteTaskStart and WriteTaskCompletion functions."""
    session = sessions.Session()
    task_start = tasks.TaskStart(session_identifier=session.identifier)
    task_completion = tasks.TaskCompletion(
        identifier=task_start.identifier,
        session_identifier=session.identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.WriteTaskStart(task_start)
      storage_file.WriteTaskCompletion(task_completion)

      storage_file.Close()

  def testVersionCompatibility(self):
    """Tests the version compatibility methods."""
    with shared_test_lib.TempDirectory() as temp_directory:
      v1_storage_path = os.path.join(temp_directory, 'v1.sqlite')
      v1_storage_file = _TestSQLiteStorageFileV1(
          storage_type=definitions.STORAGE_TYPE_SESSION)
      v1_storage_file.Open(path=v1_storage_path, read_only=False)
      v1_storage_file.Close()

      v2_storage_file_rw = _TestSQLiteStorageFileV2(
          storage_type=definitions.STORAGE_TYPE_SESSION)

      with self.assertRaises((IOError, OSError)):
        v2_storage_file_rw.Open(path=v1_storage_path, read_only=False)

      v2_storage_file_ro = _TestSQLiteStorageFileV2(
          storage_type=definitions.STORAGE_TYPE_SESSION)
      v2_storage_file_ro.Open(path=v1_storage_path, read_only=True)
      v2_storage_file_ro.Close()


if __name__ == '__main__':
  unittest.main()
