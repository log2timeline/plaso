#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the ZIP-based storage."""

import os
import unittest
import zipfile

from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.formatters import winreg   # pylint: disable=unused-import
from plaso.storage import time_range
from plaso.storage import zip_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class SerializedDataStream(test_lib.StorageTestCase):
  """Tests for the serialized data stream object."""

  # pylint: disable=protected-access

  def testReadAndSeek(self):
    """Tests the ReadEntry and SeekEntryAtOffset functions."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'event_data.000002'
    data_stream = zip_file._SerializedDataStream(
        zip_file_object, test_file, stream_name)

    self.assertEqual(data_stream.entry_index, 0)

    entry_data1 = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 1)
    self.assertEqual(data_stream._stream_offset, 671)
    self.assertIsNotNone(entry_data1)

    entry_data2 = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 2)
    self.assertEqual(data_stream._stream_offset, 1340)
    self.assertIsNotNone(entry_data2)

    # Read more entries than in the stream.
    for _ in range(3, 99):
      entry_data = data_stream.ReadEntry()

    self.assertEqual(data_stream.entry_index, 19)
    self.assertEqual(data_stream._stream_offset, 12745)
    self.assertIsNone(entry_data)

    data_stream.SeekEntryAtOffset(1, 671)
    entry_data = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 2)
    self.assertEqual(data_stream._stream_offset, 1340)
    self.assertEqual(entry_data, entry_data2)

    data_stream.SeekEntryAtOffset(0, 0)
    entry_data = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 1)
    self.assertEqual(data_stream._stream_offset, 671)
    self.assertEqual(entry_data, entry_data1)

    with self.assertRaises(IOError):
      data_stream.SeekEntryAtOffset(0, 10)
      data_stream.ReadEntry()

    stream_name = u'event_data.000009'
    data_stream = zip_file._SerializedDataStream(
        zip_file_object, test_file, stream_name)

    with self.assertRaises(IOError):
      data_stream.ReadEntry()

    zip_file_object.close()


class SerializedDataOffsetTable(test_lib.StorageTestCase):
  """Tests for the serialized data offset table object."""

  # pylint: disable=protected-access

  def testGetOffset(self):
    """Tests the GetOffset function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'event_index.000002'
    offset_table = zip_file._SerializedDataOffsetTable(
        zip_file_object, stream_name)
    offset_table.Read()

    self.assertEqual(offset_table.GetOffset(0), 0)
    self.assertEqual(offset_table.GetOffset(1), 671)

    with self.assertRaises(IndexError):
      offset_table.GetOffset(99)

    self.assertEqual(offset_table.GetOffset(-1), 12067)
    self.assertEqual(offset_table.GetOffset(-2), 11399)

    with self.assertRaises(IndexError):
      offset_table.GetOffset(-99)

  def testRead(self):
    """Tests the Read function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'event_index.000002'
    offset_table = zip_file._SerializedDataOffsetTable(
        zip_file_object, stream_name)
    offset_table.Read()

    stream_name = u'bogus'
    offset_table = zip_file._SerializedDataOffsetTable(
        zip_file_object, stream_name)

    with self.assertRaises(IOError):
      offset_table.Read()


class SerializedDataTimestampTable(test_lib.StorageTestCase):
  """Tests for the serialized data offset table object."""

  # pylint: disable=protected-access

  def testGetTimestamp(self):
    """Tests the GetTimestamp function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'event_timestamps.000002'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)
    offset_table.Read()

    self.assertEqual(offset_table.GetTimestamp(0), 1453449153000000)
    self.assertEqual(offset_table.GetTimestamp(1), 1453449153000000)

    with self.assertRaises(IndexError):
      offset_table.GetTimestamp(99)

    self.assertEqual(offset_table.GetTimestamp(-1), 1483206872000000)
    self.assertEqual(offset_table.GetTimestamp(-2), 1482083672000000)

    with self.assertRaises(IndexError):
      offset_table.GetTimestamp(-99)

  def testRead(self):
    """Tests the Read function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'event_timestamps.000002'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)
    offset_table.Read()

    stream_name = u'bogus'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)

    with self.assertRaises(IOError):
      offset_table.Read()


class ZIPStorageFileTest(test_lib.StorageTestCase):
  """Tests for the ZIP-based storage file object."""

  # pylint: disable=protected-access

  def _CreateTestStorageFileWithTags(self, path):
    """Creates a storage file with event tags for testing.

    Args:
      path: a string containing the path of the storage file.

    Returns:
      A storage file object (instance of StorageFile).
    """
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=path, read_only=False)

    test_events = self._CreateTestEvents()
    for event in test_events:
      storage_file.AddEvent(event)

    test_event_tags = self._CreateTestEventTags()
    storage_file.AddEventTags(test_event_tags[:-1])
    storage_file.AddEventTags(test_event_tags[-1:])

    storage_file.Close()

  def _GetTaggedEvent(self, storage_file, event_tag):
    """Retrieves the event object for a specific event tag.

    Args:
      storage_file: a storage file (instance of StorageFile).
      event_tag: an event tag object (instance of EventTag).

    Returns:
      An event object (instance of EventObject) or None if no corresponding
      event was found.
    """
    event = storage_file._GetEvent(
        event_tag.store_number, entry_index=event_tag.store_index)
    if not event:
      return

    event.tag = event_tag
    return event

  def testBuildTagIndex(self):
    """Tests the _BuildTagIndex function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    self.assertIsNone(storage_file._event_tag_index)

    storage_file._BuildTagIndex()

    self.assertIsNotNone(storage_file._event_tag_index)

    storage_file.Close()

  def testDeserializeAttributeContainer(self):
    """Tests the _DeserializeAttributeContainer function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    data_stream = zip_file._SerializedDataStream(
        storage_file._zipfile, storage_file._zipfile_path,
        u'event_data.000001')
    entry_data = data_stream.ReadEntry()

    attribute_container = storage_file._DeserializeAttributeContainer(
        entry_data, u'event')
    self.assertIsNotNone(attribute_container)

    storage_file.Close()

  def testGetEvent(self):
    """Tests the _GetEvent function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    # TODO: make this raise IOError.
    event = storage_file._GetEvent(0)
    self.assertIsNone(event)

    # There are 19 events in the first event data stream.
    for _ in range(0, 19):
      event = storage_file._GetEvent(1)
      self.assertIsNotNone(event)

    event = storage_file._GetEvent(1)
    self.assertIsNone(event)

    event = storage_file._GetEvent(1, entry_index=0)
    self.assertIsNotNone(event)

    event = storage_file._GetEvent(1, entry_index=15)
    self.assertIsNotNone(event)

    event = storage_file._GetEvent(1, entry_index=19)
    self.assertIsNone(event)

    with self.assertRaises(ValueError):
      storage_file._GetEvent(1, entry_index=-2)

    event = storage_file._GetEvent(3)
    self.assertIsNone(event)

    storage_file.Close()

  def testGetEventObjectSerializedData(self):
    """Tests the _GetEventSerializedData function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    # TODO: make this raise IOError.
    data_tuple = storage_file._GetEventSerializedData(0)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    self.assertIsNone(data_tuple[1])

    # There are 19 events in the first event data stream.
    for entry_index in range(0, 19):
      data_tuple = storage_file._GetEventSerializedData(1)
      self.assertIsNotNone(data_tuple)
      self.assertIsNotNone(data_tuple[0])
      self.assertEqual(data_tuple[1], entry_index)

    data_tuple = storage_file._GetEventSerializedData(1)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    self.assertEqual(data_tuple[1], 19)

    data_tuple = storage_file._GetEventSerializedData(1, entry_index=0)
    self.assertIsNotNone(data_tuple)
    self.assertIsNotNone(data_tuple[0])
    self.assertEqual(data_tuple[1], 0)

    data_tuple = storage_file._GetEventSerializedData(1, entry_index=15)
    self.assertIsNotNone(data_tuple)
    self.assertIsNotNone(data_tuple[0])
    self.assertEqual(data_tuple[1], 15)

    data_tuple = storage_file._GetEventSerializedData(1, entry_index=19)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    # TODO: make the behavior of this method more consistent.
    self.assertIsNone(data_tuple[1])

    with self.assertRaises(ValueError):
      storage_file._GetEventSerializedData(1, entry_index=-2)

    data_tuple = storage_file._GetEventSerializedData(3)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    # TODO: make the behavior of this method more consistent.
    self.assertIsNone(data_tuple[1])

    storage_file.Close()

  def testGetEventSource(self):
    """Tests the _GetEventSource function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    # TODO: make this raise IOError.
    event_source = storage_file._GetEventSource(0)
    self.assertIsNone(event_source)

    # There is 1 event source in the first event data stream.
    for _ in range(0, 1):
      event_source = storage_file._GetEventSource(1)
      self.assertIsNotNone(event_source)

    event_source = storage_file._GetEventSource(1)
    self.assertIsNone(event_source)

    event_source = storage_file._GetEventSource(1, entry_index=0)
    self.assertIsNotNone(event_source)

    event_source = storage_file._GetEventSource(1, entry_index=1)
    self.assertIsNone(event_source)

    with self.assertRaises(ValueError):
      storage_file._GetEventSource(1, entry_index=-2)

    event_source = storage_file._GetEventSource(3)
    self.assertIsNone(event_source)

    storage_file.Close()

  def testGetEventSourceSerializedData(self):
    """Tests the _GetEventSourceSerializedData function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    # TODO: make this raise IOError.
    data_tuple = storage_file._GetEventSourceSerializedData(0)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    self.assertIsNone(data_tuple[1])

    # There is 1 event source in the first event data stream.
    for entry_index in range(0, 1):
      data_tuple = storage_file._GetEventSourceSerializedData(1)
      self.assertIsNotNone(data_tuple)
      self.assertIsNotNone(data_tuple[0])
      self.assertEqual(data_tuple[1], entry_index)

    data_tuple = storage_file._GetEventSourceSerializedData(1)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    self.assertEqual(data_tuple[1], 1)

    data_tuple = storage_file._GetEventSourceSerializedData(1, entry_index=0)
    self.assertIsNotNone(data_tuple)
    self.assertIsNotNone(data_tuple[0])
    self.assertEqual(data_tuple[1], 0)

    data_tuple = storage_file._GetEventSourceSerializedData(1, entry_index=2)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    # TODO: make the behavior of this method more consistent.
    self.assertIsNone(data_tuple[1])

    with self.assertRaises(ValueError):
      storage_file._GetEventSourceSerializedData(1, entry_index=-2)

    data_tuple = storage_file._GetEventSourceSerializedData(3)
    self.assertIsNotNone(data_tuple)
    self.assertIsNone(data_tuple[0])
    # TODO: make the behavior of this method more consistent.
    self.assertIsNone(data_tuple[1])

    storage_file.Close()

  def testGetLastStreamNumber(self):
    """Tests the _GetLastStreamNumber function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    last_stream_number = storage_file._GetLastStreamNumber(u'event_data')
    self.assertEqual(last_stream_number, 3)

    last_stream_number = storage_file._GetLastStreamNumber(
        u'event_source_data')
    self.assertEqual(last_stream_number, 3)

    last_stream_number = storage_file._GetLastStreamNumber(u'bogus')
    self.assertEqual(last_stream_number, 1)

    storage_file.Close()

  # TODO: add test for _InitializeMergeBuffer.

  def testGetSerializedDataStream(self):
    """Tests the _GetSerializedDataStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    data_stream = storage_file._GetSerializedDataStream(
        storage_file._event_streams, u'event_data', 2)
    self.assertIsNotNone(data_stream)

    with self.assertRaises(IOError):
      storage_file._GetSerializedDataStream(
          storage_file._event_streams, u'event_data', 99)

    with self.assertRaises(IOError):
      storage_file._GetSerializedDataStream(
          storage_file._event_streams, u'bogus', 1)

    storage_file.Close()

  def testGetSerializedDataOffsetTable(self):
    """Tests the _GetSerializedDataOffsetTable function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    offset_table = storage_file._GetSerializedDataOffsetTable(
        storage_file._event_offset_tables,
        storage_file._event_offset_tables_lfu,
        u'event_index', 2)
    self.assertIsNotNone(offset_table)

    with self.assertRaises(IOError):
      storage_file._GetSerializedDataOffsetTable(
          storage_file._event_offset_tables,
          storage_file._event_offset_tables_lfu,
          u'event_index', 99)

    storage_file.Close()

  def testGetSerializedDataStreamNumbers(self):
    """Tests the _GetSerializedDataStreamNumbers function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    data_stream_numbers = storage_file._GetSerializedDataStreamNumbers(
        u'event_data')
    self.assertEqual(data_stream_numbers, [1, 2])

    storage_file.Close()

  def testGetSerializedEventOffsetTable(self):
    """Tests the _GetSerializedEventOffsetTable function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    offset_table = storage_file._GetSerializedEventOffsetTable(2)
    self.assertIsNotNone(offset_table)

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventOffsetTable(99)

    storage_file.Close()

  def testGetSerializedEventSourceOffsetTable(self):
    """Tests the _GetSerializedEventSourceOffsetTable function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    # TODO: add positive test.

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventSourceOffsetTable(99)

    storage_file.Close()

  def testGetSerializedEventSourceStream(self):
    """Tests the _GetSerializedEventSourceStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    # TODO: add positive test.

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventSourceStream(99)

    storage_file.Close()

  def testGetSerializedEventStream(self):
    """Tests the _GetSerializedEventStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    data_stream = storage_file._GetSerializedEventStream(2)
    self.assertIsNotNone(data_stream)

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventStream(99)

    storage_file.Close()

  def testGetSerializedEventSourceStreamNumbers(self):
    """Tests the _GetSerializedEventSourceStreamNumbers function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    stream_numbers = storage_file._GetSerializedEventSourceStreamNumbers()
    self.assertEqual(len(stream_numbers), 2)

    storage_file.Close()

  def testGetSerializedEventStreamNumbers(self):
    """Tests the _GetSerializedEventStreamNumbers function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    stream_numbers = storage_file._GetSerializedEventStreamNumbers()
    self.assertEqual(len(stream_numbers), 2)

    storage_file.Close()

  def testGetSerializedEventTimestampTable(self):
    """Tests the _GetSerializedEventTimestampTable function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    timestamp_table = storage_file._GetSerializedEventTimestampTable(2)
    self.assertIsNotNone(timestamp_table)

    storage_file.Close()

  def testGetStreamNames(self):
    """Tests the _GetStreamNames function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    stream_names = list(storage_file._GetStreamNames())
    self.assertEqual(len(stream_names), 31)

    storage_file.Close()

  def testGetSortedEvent(self):
    """Tests the _GetSortedEvent function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    expected_timestamp = 1453449153000000

    event = storage_file._GetSortedEvent()
    self.assertIsNotNone(event)
    self.assertEqual(event.timestamp, expected_timestamp)

    # Test lower bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'),
        timelib.Timestamp.CopyFromString(u'2030-12-31 23:59:59'))

    storage_file.Close()

    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    expected_timestamp = 1476630823000000

    event = storage_file._GetSortedEvent(time_range=test_time_range)
    self.assertEqual(event.timestamp, expected_timestamp)

    # Test upper bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2000-01-01 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'))

    storage_file.Close()

    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    expected_timestamp = 1453449153000000

    event = storage_file._GetSortedEvent(time_range=test_time_range)
    self.assertEqual(event.timestamp, expected_timestamp)

    storage_file.Close()

  def testHasStream(self):
    """Tests the _HasStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    self.assertTrue(storage_file._HasStream(u'event_timestamps.000002'))
    self.assertFalse(storage_file._HasStream(u'bogus'))

    storage_file.Close()

  def testOpenStream(self):
    """Tests the _OpenStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    file_object = storage_file._OpenStream(u'event_timestamps.000002')
    self.assertIsNotNone(file_object)

    file_object = storage_file._OpenStream(u'bogus')
    self.assertIsNone(file_object)

    storage_file.Close()

  def testOpenZIPFile(self):
    """Tests the _OpenZIPFile, _OpenRead and _OpenWrite functions."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()

    storage_file._OpenZIPFile(test_file, True)
    storage_file._OpenRead()

    storage_file.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file._OpenZIPFile(temp_file, False)
      storage_file._OpenRead()
      storage_file._OpenWrite()

      storage_file.Close()

  def testReadAttributeContainerFromStreamEntry(self):
    """Tests the _ReadAttributeContainerFromStreamEntry function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    data_stream = zip_file._SerializedDataStream(
        storage_file._zipfile, storage_file._zipfile_path,
        u'event_data.000001')

    attribute_container = storage_file._ReadAttributeContainerFromStreamEntry(
        data_stream, u'event')
    self.assertIsNotNone(attribute_container)

    storage_file.Close()

  def testReadAttributeContainersFromStream(self):
    """Tests the _ReadAttributeContainersFromStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    data_stream = zip_file._SerializedDataStream(
        storage_file._zipfile, storage_file._zipfile_path,
        u'event_data.000001')

    attribute_containers = list(
        storage_file._ReadAttributeContainersFromStream(data_stream, u'event'))
    self.assertEqual(len(attribute_containers), 19)

    storage_file.Close()

  def testReadEventTagByIdentifier(self):
    """Tests the _ReadEventTagByIdentifier function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file)

      event_tag = storage_file._ReadEventTagByIdentifier(0, 0, u'')
      self.assertIsNone(event_tag)

      # TODO: add positive test.

      storage_file.Close()

  def testReadSerializerStream(self):
    """Tests the _ReadSerializerStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    # Serializer stream is used by the old format.
    serialization_format = storage_file._ReadSerializerStream()
    self.assertIsNone(serialization_format)

    # TODO: add old format test file or remove this functionality.

    storage_file.Close()

  def testReadStorageMetadata(self):
    """Tests the _ReadStorageMetadata function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    self.assertTrue(storage_file._ReadStorageMetadata())

    storage_file.Close()

  def testReadStream(self):
    """Tests the _ReadStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    stream_data = storage_file._ReadStream(u'event_timestamps.000002')
    self.assertNotEqual(stream_data, b'')

    stream_data = storage_file._ReadStream(u'bogus')
    self.assertEqual(stream_data, b'')

    storage_file.Close()

  # TODO: add test for _SerializeAttributeContainer.
  # TODO: add test for _WriteAttributeContainersHeap.

  def testWriteSerializedErrors(self):
    """Tests the _WriteSerializedErrors function."""
    extraction_error = errors.ExtractionError(
        message=u'Test extraction error')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddError(extraction_error)

      storage_file._WriteSerializedErrors()

      storage_file.Close()

  def testWriteSerializedEvents(self):
    """Tests the _WriteSerializedEvents function."""
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      storage_file._WriteSerializedEvents()

      storage_file.Close()

  def testWriteSerializedEventSources(self):
    """Tests the _WriteSerializedEventSources function."""
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddEventSource(event_source)

      storage_file._WriteSerializedEventSources()

      storage_file.Close()

  def testWriteSerializedEventTags(self):
    """Tests the _WriteSerializedEventTags function."""
    test_events = self._CreateTestEvents()
    event_tags = self._CreateTestEventTags()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      for event_tag in event_tags:
        storage_file.AddEventTag(event_tag)

      storage_file._WriteSerializedEvents()
      storage_file._WriteSerializedEventTags()

      storage_file.Close()

  # The _WriteSessionStart and _WriteSessionCompletion functions at tested by
  # WriteSessionStart and WriteSessionCompletion.

  def testWriteStorageMetadata(self):
    """Tests the _WriteStorageMetadata function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file._WriteStorageMetadata()

      storage_file.Close()

  def testWriteStream(self):
    """Tests the _WriteStream function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file._WriteStream(u'bogus', b'test')

      storage_file.Close()

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file)

      stream_data = storage_file._ReadStream(u'bogus')
      self.assertEqual(stream_data, b'test')

      storage_file.Close()

  # The _WriteTaskStart and _WriteTaskCompletion functions at tested by
  # WriteTaskStart and WriteTaskCompletion.

  def testAddAnalysisReport(self):
    """Tests the AddAnalysisReport function."""
    analysis_report = reports.AnalysisReport(
        plugin_name=u'test', text=u'test report')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddAnalysisReport(analysis_report)

      storage_file.Close()

  def testAddError(self):
    """Tests the AddError function."""
    extraction_error = errors.ExtractionError(
        message=u'Test extraction error')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddError(extraction_error)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddError.

  def testAddEvent(self):
    """Tests the AddEvent function."""
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddEvent.

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddEventSource(event_source)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddEventSource.

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    test_events = self._CreateTestEvents()
    event_tags = self._CreateTestEventTags()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      for event_tag in event_tags:
        storage_file.AddEventTag(event_tag)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddEventTag.

  def testAddEventTags(self):
    """Tests the AddEventTags function."""
    test_events = self._CreateTestEvents()
    event_tags = self._CreateTestEventTags()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      storage_file.AddEventTags(event_tags[:-1])
      storage_file.AddEventTags(event_tags[-1:])

      storage_file.Close()

  def testGetAnalysisReports(self):
    """Tests the GetAnalysisReports function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    analysis_reports = list(storage_file.GetAnalysisReports())
    self.assertEqual(len(analysis_reports), 2)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    test_reports = list(storage_file.GetAnalysisReports())
    self.assertEqual(len(test_reports), 0)

    storage_file.Close()

  def testGetErrors(self):
    """Tests the GetErrors function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    test_errors = list(storage_file.GetErrors())
    self.assertEqual(len(test_errors), 2)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    test_errors = list(storage_file.GetErrors())
    self.assertEqual(len(test_errors), 0)

    storage_file.Close()

  def testGetEvents(self):
    """Tests the GetEvents function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    test_events = list(storage_file.GetEvents())
    self.assertEqual(len(test_events), 38)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    test_events = list(storage_file.GetEvents())
    self.assertEqual(len(test_events), 3)

    storage_file.Close()

  def testGetEventSourceByIndex(self):
    """Tests the GetEventSourceByIndex function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    event_source = storage_file.GetEventSourceByIndex(1)
    self.assertIsNotNone(event_source)

    event_source = storage_file.GetEventSourceByIndex(2)
    self.assertIsNone(event_source)

    event_source = storage_file.GetEventSourceByIndex(0)
    self.assertIsNotNone(event_source)

    storage_file.Close()

  def testGetEventSources(self):
    """Tests the GetEventSources function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    test_event_sources = list(storage_file.GetEventSources())
    self.assertEqual(len(test_event_sources), 2)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    test_event_sources = list(storage_file.GetEventSources())
    self.assertEqual(len(test_event_sources), 2)

    storage_file.Close()

  def testGetEventTags(self):
    """Tests the GetEventTags function."""
    formatter_mediator = formatters_mediator.FormatterMediator()

    tagged_events = []

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file)

      for event_tag in storage_file.GetEventTags():
        event = self._GetTaggedEvent(storage_file, event_tag)
        tagged_events.append(event)

      storage_file.Close()

    self.assertEqual(len(tagged_events), 4)

    event = tagged_events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-04-05 12:27:39')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.tag.comment, u'My comment')

    message, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event)
    self.assertEqual(message[0:10], u'This is a ')

    event = tagged_events[1]
    self.assertEqual(event.tag.labels[0], u'Malware')
    message, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event)
    self.assertEqual(message[0:14], u'[HKCU\\Windows\\')

    event = tagged_events[2]
    self.assertEqual(event.tag.comment, u'This is interesting')
    self.assertEqual(event.tag.labels[0], u'Malware')
    self.assertEqual(event.tag.labels[1], u'Benign')

    self.assertEqual(event.parser, u'UNKNOWN')

    # Test the newly added fourth tag, which should include data from
    # the first version as well.
    event = tagged_events[3]
    self.assertEqual(event.tag.labels[0], u'Interesting')
    self.assertEqual(event.tag.labels[1], u'Malware')

  def testGetNumberOfAnalysisReports(self):
    """Tests the GetNumberOfAnalysisReports function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    number_of_event_sources = storage_file.GetNumberOfAnalysisReports()
    self.assertEqual(number_of_event_sources, 2)

    storage_file.Close()

  def testGetNumberOfEventSources(self):
    """Tests the GetNumberOfEventSources function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    number_of_event_sources = storage_file.GetNumberOfEventSources()
    self.assertEqual(number_of_event_sources, 2)

    storage_file.Close()

  def testGetSessions(self):
    """Tests the GetSessions function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    sessions_list = list(storage_file.GetSessions())
    self.assertEqual(len(sessions_list), 4)

    storage_file.Close()

  def testHasAnalysisReports(self):
    """Tests the HasAnalysisReports function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    has_reports = storage_file.HasAnalysisReports()
    self.assertTrue(has_reports)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    has_reports = storage_file.HasAnalysisReports()
    self.assertFalse(has_reports)

    storage_file.Close()

  def testHasErrors(self):
    """Tests the HasErrors function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    self.assertTrue(storage_file.HasErrors())

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    self.assertFalse(storage_file.HasErrors())

    storage_file.Close()

  def testHasEventTags(self):
    """Tests the HasEventTags function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    self.assertTrue(storage_file.HasEventTags())

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)

    self.assertFalse(storage_file.HasEventTags())

    storage_file.Close()

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    # Read-only of session storage.
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path=test_file)
    storage_file.Close()

    # Write append of session storage.
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)
      storage_file.Close()

      storage_file.Open(path=temp_file, read_only=False)
      storage_file.Close()

      storage_file.Open(path=temp_file)
      storage_file.Close()

    # Write append of task storage.
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(path=temp_file, read_only=False)
      storage_file.Close()

      storage_file.Open(path=temp_file, read_only=False)
      storage_file.Close()

      storage_file.Open(path=temp_file)
      storage_file.Close()

  def testWriteSessionStartAndCompletion(self):
    """Tests the WriteSessionStart and WriteSessionCompletion functions."""
    session = sessions.Session()
    session_start = session.CreateSessionStart()
    session_completion = session.CreateSessionCompletion()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.WriteSessionStart(session_start)
      storage_file.WriteSessionCompletion(session_completion)

      storage_file.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(path=temp_file, read_only=False)

      with self.assertRaises(IOError):
        storage_file.WriteSessionStart(session_start)

      with self.assertRaises(IOError):
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
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.WriteTaskStart(task_start)
      storage_file.WriteTaskCompletion(task_completion)

      storage_file.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      with self.assertRaises(IOError):
        storage_file.WriteTaskStart(task_start)

      with self.assertRaises(IOError):
        storage_file.WriteTaskCompletion(task_completion)

      storage_file.Close()


class ZIPStorageFileReaderTest(test_lib.StorageTestCase):
  """Tests for the ZIP-based storage file reader object."""

  _EXPECTED_TIMESTAMPS_BEFORE_20060430 = [
      1453449153000000, 1453449153000000, 1453449153000000, 1453449153000000,
      1453449181000000, 1453449181000000, 1453449241000000, 1453449241000000,
      1453449241000000, 1453449241000000, 1453449272000000, 1453449272000000,
      1454771790000000, 1454771790000000, 1456708543000000, 1456708543000000,
      1458774078000000, 1458774078000000, 1458774078000000, 1458774078000000]

  _EXPECTED_TIMESTAMPS_AFTER_20060430 = [
      1476630823000000, 1476630823000000, 1476630823000000, 1476630823000000,
      1476630824000000, 1476630824000000, 1479431720000000, 1479431720000000,
      1479431743000000, 1479431743000000, 1479457820000000, 1479457820000000,
      1479457880000000, 1479457880000000, 1482083672000000, 1482083672000000,
      1483206872000000, 1483206872000000]

  def testGetEvents(self):
    """Tests the GetEvents function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    timestamps = []
    with zip_file.ZIPStorageFileReader(test_file) as storage_reader:
      for event in storage_reader.GetEvents():
        timestamps.append(event.timestamp)

    expected_timestamps = []
    expected_timestamps.extend(self._EXPECTED_TIMESTAMPS_BEFORE_20060430)
    expected_timestamps.extend(self._EXPECTED_TIMESTAMPS_AFTER_20060430)

    print sorted(timestamps)
    self.assertEqual(len(timestamps), 38)
    self.assertEqual(sorted(timestamps), expected_timestamps)

    # Test lower bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'),
        timelib.Timestamp.CopyFromString(u'2030-12-31 23:59:59'))

    timestamps = []
    with zip_file.ZIPStorageFileReader(test_file) as storage_reader:
      for event in storage_reader.GetEvents(time_range=test_time_range):
        timestamps.append(event.timestamp)

    expected_timestamps = self._EXPECTED_TIMESTAMPS_AFTER_20060430

    self.assertEqual(sorted(timestamps), expected_timestamps)

    # Test upper bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2000-01-01 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'))

    timestamps = []
    with zip_file.ZIPStorageFileReader(test_file) as storage_reader:
      for event in storage_reader.GetEvents(time_range=test_time_range):
        timestamps.append(event.timestamp)

    expected_timestamps = self._EXPECTED_TIMESTAMPS_BEFORE_20060430

    self.assertEqual(sorted(timestamps), expected_timestamps)

  # TODO: add test for GetEventSources.


class ZIPStorageFileWriterTest(test_lib.StorageTestCase):
  """Tests for the ZIP-based storage file writer object."""

  def testAddAnalysisReport(self):
    """Tests the AddAnalysisReport function."""
    session = sessions.Session()
    analysis_report = reports.AnalysisReport(
        plugin_name=u'test', text=u'test report')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      storage_writer.AddAnalysisReport(analysis_report)

      storage_writer.Close()

  def testAddError(self):
    """Tests the AddError function."""
    session = sessions.Session()
    extraction_error = errors.ExtractionError(
        message=u'Test extraction error')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      storage_writer.AddError(extraction_error)

      storage_writer.Close()

  def testAddEvent(self):
    """Tests the AddEvent function."""
    session = sessions.Session()
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      for event in test_events:
        storage_writer.AddEvent(event)

      storage_writer.Close()

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    session = sessions.Session()
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      storage_writer.AddEventSource(event_source)

      storage_writer.Close()

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    session = sessions.Session()
    test_events = self._CreateTestEvents()
    event_tags = self._CreateTestEventTags()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      for event in test_events:
        storage_writer.AddEvent(event)

      for event_tag in event_tags:
        storage_writer.AddEventTag(event_tag)

      storage_writer.Close()

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    session = sessions.Session()
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()
      storage_writer.Close()

      storage_writer.Open()
      storage_writer.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(
          session, temp_file, storage_type=definitions.STORAGE_TYPE_TASK)
      storage_writer.Open()
      storage_writer.Close()

      storage_writer.Open()
      storage_writer.Close()

  # TODO: add test for GetEvents.
  # TODO: add test for GetFirstWrittenEventSource and GetNextWrittenEventSource.

  def testMergeFromStorage(self):
    """Tests the MergeFromStorage function."""
    session = sessions.Session()
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
      storage_reader = zip_file.ZIPStorageFileReader(test_file)
      storage_writer.MergeFromStorage(storage_reader)

      test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
      storage_reader = zip_file.ZIPStorageFileReader(test_file)
      storage_writer.MergeFromStorage(storage_reader)

      storage_writer.Close()

  def testWriteSessionStartAndCompletion(self):
    """Tests the WriteSessionStart and WriteSessionCompletion functions."""
    session = sessions.Session()
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      storage_writer.WriteSessionStart()
      storage_writer.WriteSessionCompletion()

      storage_writer.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(
          session, temp_file, storage_type=definitions.STORAGE_TYPE_TASK)
      storage_writer.Open()

      with self.assertRaises(IOError):
        storage_writer.WriteSessionStart()

      with self.assertRaises(IOError):
        storage_writer.WriteSessionCompletion()

      storage_writer.Close()

  def testWriteTaskStartAndCompletion(self):
    """Tests the WriteTaskStart and WriteTaskCompletion functions."""
    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(
          session, temp_file, storage_type=definitions.STORAGE_TYPE_TASK,
          task=task)
      storage_writer.Open()

      storage_writer.WriteTaskStart()
      storage_writer.WriteTaskCompletion()

      storage_writer.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      storage_writer.Open()

      with self.assertRaises(IOError):
        storage_writer.WriteTaskStart()

      with self.assertRaises(IOError):
        storage_writer.WriteTaskCompletion()

      storage_writer.Close()

  def testStartMergeTaskStorage(self):
    """Tests the StartMergeTaskStorage functions."""
    session = sessions.Session()
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      session_storage_writer = zip_file.ZIPStorageFileWriter(session, temp_file)
      session_storage_writer.Open()

      session_storage_writer.WriteSessionStart()

      session_storage_writer.StartTaskStorage()

      # Test a complete task merge.
      task = tasks.Task(session_identifier=session.identifier)
      task_storage_writer = session_storage_writer.CreateTaskStorage(task)
      task_storage_writer.Open()
      task_storage_writer.WriteTaskStart()

      for event in test_events:
        task_storage_writer.AddEvent(event)

      task_storage_writer.WriteTaskCompletion()
      task_storage_writer.Close()

      self.assertEqual(task_storage_writer.number_of_events, 4)

      merge_ready = session_storage_writer.CheckTaskReadyForMerge(task)
      self.assertFalse(merge_ready)
      self.assertIsNone(task.storage_file_size)

      session_storage_writer.PrepareMergeTaskStorage(task)

      merge_ready = session_storage_writer.CheckTaskReadyForMerge(task)
      self.assertTrue(merge_ready)
      self.assertIsNotNone(task.storage_file_size)

      storage_merge_reader = session_storage_writer.StartMergeTaskStorage(task)
      self.assertIsNotNone(storage_merge_reader)

      fully_merged = storage_merge_reader.MergeAttributeContainers()
      self.assertTrue(fully_merged)

      self.assertEqual(session_storage_writer.number_of_events, 4)

      merge_ready = session_storage_writer.CheckTaskReadyForMerge(task)
      self.assertFalse(merge_ready)

      # Test an incomplete task merge.
      task = tasks.Task(session_identifier=session.identifier)
      task_storage_writer = session_storage_writer.CreateTaskStorage(task)
      task_storage_writer.Open()
      task_storage_writer.WriteTaskStart()

      for event in test_events:
        task_storage_writer.AddEvent(event)

      task_storage_writer.Close()

      self.assertEqual(task_storage_writer.number_of_events, 4)

      session_storage_writer.PrepareMergeTaskStorage(task)

      merge_ready = session_storage_writer.CheckTaskReadyForMerge(task)
      self.assertTrue(merge_ready)
      self.assertIsNotNone(task.storage_file_size)

      storage_merge_reader = session_storage_writer.StartMergeTaskStorage(task)
      self.assertIsNotNone(storage_merge_reader)

      fully_merged = storage_merge_reader.MergeAttributeContainers()
      self.assertTrue(fully_merged)

      self.assertEqual(session_storage_writer.number_of_events, 8)

      session_storage_writer.StopTaskStorage()

      session_storage_writer.WriteSessionCompletion()

      session_storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
