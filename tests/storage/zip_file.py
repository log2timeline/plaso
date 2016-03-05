#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the event storage."""

import os
import unittest
import zipfile

from plaso.engine import queue
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.formatters import winreg   # pylint: disable=unused-import
from plaso.multi_processing import multi_process
from plaso.serializer import protobuf_serializer
from plaso.storage import time_range
from plaso.storage import zip_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class DummyObject(object):
  """Dummy object."""


class SerializedDataStream(test_lib.StorageTestCase):
  """Tests for the serialized data stream object."""

  def testReadAndSeek(self):
    """Tests the ReadEntry and SeekEntryAtOffset functions."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_proto.000003'
    data_stream = zip_file._SerializedDataStream(
        zip_file_object, test_file, stream_name)

    # The plaso_index.000003 stream contains 2 protobuf serialized
    # event objects. One at offset 0 of size 271 (including the 4 bytes of
    # the entry size) and one at offset 271 of size 271.
    self.assertEqual(data_stream.entry_index, 0)

    entry_data1 = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 1)
    self.assertEqual(data_stream._stream_offset, 271)
    self.assertIsNotNone(entry_data1)

    entry_data2 = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 2)
    self.assertEqual(data_stream._stream_offset, 542)
    self.assertIsNotNone(entry_data2)

    entry_data = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 2)
    self.assertEqual(data_stream._stream_offset, 542)
    self.assertIsNone(entry_data)

    data_stream.SeekEntryAtOffset(1, 271)
    entry_data = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 2)
    self.assertEqual(data_stream._stream_offset, 542)
    self.assertEqual(entry_data, entry_data2)

    data_stream.SeekEntryAtOffset(0, 0)
    entry_data = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 1)
    self.assertEqual(data_stream._stream_offset, 271)
    self.assertEqual(entry_data, entry_data1)

    with self.assertRaises(IOError):
      data_stream.SeekEntryAtOffset(0, 10)
      data_stream.ReadEntry()

    stream_name = u'plaso_proto.000009'
    data_stream = zip_file._SerializedDataStream(
        zip_file_object, test_file, stream_name)

    with self.assertRaises(IOError):
      data_stream.ReadEntry()

    zip_file_object.close()


class SerializedDataOffsetTable(test_lib.StorageTestCase):
  """Tests for the serialized data offset table object."""

  def testGetOffset(self):
    """Tests the GetOffset function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_index.000003'
    offset_table = zip_file._SerializedDataOffsetTable(
        zip_file_object, stream_name)
    offset_table.Read()

    self.assertEqual(offset_table.GetOffset(0), 0)
    self.assertEqual(offset_table.GetOffset(1), 271)

    with self.assertRaises(IndexError):
      offset_table.GetOffset(2)

    self.assertEqual(offset_table.GetOffset(-1), 271)
    self.assertEqual(offset_table.GetOffset(-2), 0)

    with self.assertRaises(IndexError):
      offset_table.GetOffset(-3)

  def testRead(self):
    """Tests the Read function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_index.000003'
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

  def testGetTimestamp(self):
    """Tests the GetTimestamp function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_timestamps.000003'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)
    offset_table.Read()

    self.assertEqual(offset_table.GetTimestamp(0), 1390377181000000)
    self.assertEqual(offset_table.GetTimestamp(1), 1390377241000000)

    with self.assertRaises(IndexError):
      offset_table.GetTimestamp(2)

    self.assertEqual(offset_table.GetTimestamp(-1), 1390377241000000)
    self.assertEqual(offset_table.GetTimestamp(-2), 1390377181000000)

    with self.assertRaises(IndexError):
      offset_table.GetTimestamp(-3)

  def testRead(self):
    """Tests the Read function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_timestamps.000003'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)
    offset_table.Read()

    stream_name = u'bogus'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)

    with self.assertRaises(IOError):
      offset_table.Read()


class ZIPStorageFile(test_lib.StorageTestCase):
  """Tests for the ZIP-based storage file object."""

  def testGetSerializedEventObjectOffsetTable(self):
    """Tests the _GetSerializedEventObjectOffsetTable function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    offset_table = storage_file._GetSerializedEventObjectOffsetTable(3)
    self.assertIsNotNone(offset_table)

    storage_file.Close()

  def testGetSerializedEventObjectStream(self):
    """Tests the _GetSerializedEventObjectStream function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    data_stream = storage_file._GetSerializedEventObjectStream(3)
    self.assertIsNotNone(data_stream)

    storage_file.Close()

  def testGetSerializedEventObjectStreamNumbers(self):
    """Tests the _GetSerializedEventObjectStreamNumbers function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    stream_numbers = storage_file._GetSerializedEventObjectStreamNumbers()
    self.assertEqual(len(stream_numbers), 7)

    storage_file.Close()

  def testGetSerializedEventObjectTimestampTable(self):
    """Tests the _GetSerializedEventObjectTimestampTable function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamp_table = storage_file._GetSerializedEventObjectTimestampTable(3)
    self.assertIsNotNone(timestamp_table)

    storage_file.Close()

  def testGetStreamNames(self):
    """Tests the _GetStreamNames function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    stream_names = list(storage_file._GetStreamNames())
    self.assertEqual(len(stream_names), 29)

    storage_file.Close()

  def testHasStream(self):
    """Tests the _HasStream function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    self.assertTrue(storage_file._HasStream(u'plaso_timestamps.000003'))
    self.assertFalse(storage_file._HasStream(u'bogus'))

    storage_file.Close()

  # TODO: add _OpenStream test.
  # TODO: add _ReadStream test.
  # TODO: add _WriteStream test.


class StorageFileTest(test_lib.StorageTestCase):
  """Tests for the ZIP storage file object."""

  def _CreateTestEventTags(self):
    """Creates the event tags for testing.

    Returns:
      A list of event tags (instances of EventTag).
    """
    event_tags = []

    event_tag = event.EventTag()
    event_tag.store_index = 0
    event_tag.store_number = 1
    event_tag.comment = u'My comment'
    event_tags.append(event_tag)

    event_tag = event.EventTag()
    event_tag.store_index = 1
    event_tag.store_number = 1
    event_tag.AddLabel(u'Malware')
    event_tags.append(event_tag)

    event_tag = event.EventTag()
    event_tag.store_number = 1
    event_tag.store_index = 2
    event_tag.comment = u'This is interesting'
    event_tag.AddLabels([u'Malware', u'Benign'])
    event_tags.append(event_tag)

    event_tag = event.EventTag()
    event_tag.store_index = 1
    event_tag.store_number = 1
    event_tag.AddLabel(u'Interesting')
    event_tags.append(event_tag)

    return event_tags

  def _CreateTestStorageFileWithTags(self, path):
    """Creates a storage file with event tags for testing.

    Args:
      path: a string containing the path of the storage file.

    Returns:
      A storage file object (instance of StorageFile).
    """
    test_event_objects = test_lib.CreateTestEventObjects()
    test_event_tags = self._CreateTestEventTags()

    storage_file = zip_file.StorageFile(path)
    for test_event_object in test_event_objects:
      storage_file.AddEventObject(test_event_object)

    storage_file.StoreTagging(test_event_tags[:-1])
    storage_file.StoreTagging(test_event_tags[-1:])

    preprocessing_object = event.PreprocessObject()
    storage_file.WritePreprocessObject(preprocessing_object)

    storage_file.Close()

  def _GetEventObjects(self, storage_file, stream_number):
    """Retrieves all the event object in specific serialized data stream.

    Args:
      storage_file: a storage file (instance of StorageFile).
      stream_number: an integer containing the number of the serialized event
                     object stream.

    Yields:
      An event object (instance of EventObject).
    """
    event_object = storage_file._GetEventObject(stream_number)
    while event_object:
      yield event_object
      event_object = storage_file._GetEventObject(stream_number)

  def _GetEventsFromGroup(self, storage_file, event_group):
    """Return a generator with all EventObjects from a group.

    Args:
      storage_file: a storage file (instance of StorageFile).
      event_group: an event group (instance of plaso_storage_pb2.EventGroup).

    Returns:
      A list of event objects (instance of EventObjects).
    """
    event_objects = []
    for group_event in event_group.events:
      event_object = storage_file._GetEventObject(
          group_event.store_number, entry_index=group_event.store_index)
      event_objects.append(event_object)

    return event_objects

  def _GetTaggedEvent(self, storage_file, event_tag):
    """Retrieves the event object for a specific event tag.

    Args:
      storage_file: a storage file (instance of StorageFile).
      event_tag: an event tag object (instance of EventTag).

    Returns:
      An event object (instance of EventObject) or None if no corresponding
      event was found.
    """
    event_object = storage_file._GetEventObject(
        event_tag.store_number, entry_index=event_tag.store_index)
    if not event_object:
      return

    event_object.tag = event_tag
    return event_object

  # TODO: add test for _ReadEventTag
  # TODO: add test for _ReadEventTagByIdentifier

  def testAddEventObject(self):
    """Tests the AddEventObject function."""
    test_event_objects = test_lib.CreateTestEventObjects()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      storage_file = zip_file.StorageFile(temp_file)

      for test_event_object in test_event_objects:
        storage_file.AddEventObject(test_event_object)

      storage_file.Close()

  # TODO: add test for GetReports

  def testGetSortedEntry(self):
    """Tests the GetSortedEntry function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    expected_timestamp = 1343166324000000

    event_object = storage_file.GetSortedEntry()
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Test lower bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2014-02-16 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2030-12-31 23:59:59'))

    storage_file.Close()

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    expected_timestamp = 1418925272000000

    event_object = storage_file.GetSortedEntry(time_range=test_time_range)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Test upper bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2000-01-01 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2014-02-16 00:00:00'))

    storage_file.Close()

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    expected_timestamp = 1343166324000000

    event_object = storage_file.GetSortedEntry(time_range=test_time_range)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    storage_file.Close()

  def testGetStorageInformation(self):
    """Tests the GetStorageInformation function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    storage_information = storage_file.GetStorageInformation()
    self.assertEqual(len(storage_information), 1)

    storage_file.Close()

  def testGetTagging(self):
    """Tests the GetTagging function."""
    formatter_mediator = formatters_mediator.FormatterMediator()

    tagged_event_objects = []

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = zip_file.StorageFile(temp_file, read_only=True)

      for tag in storage_file.GetTagging():
        event_object = self._GetTaggedEvent(storage_file, tag)
        tagged_event_objects.append(event_object)

      storage_file.Close()

    self.assertEqual(len(tagged_event_objects), 4)

    event_object = tagged_event_objects[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-04-05 12:27:39')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.store_number, 1)
    self.assertEqual(event_object.store_index, 0)
    self.assertEqual(event_object.tag.comment, u'My comment')

    message, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)
    self.assertEqual(message[0:10], u'This is a ')

    event_object = tagged_event_objects[1]
    self.assertEqual(event_object.tag.labels[0], u'Malware')
    message, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)
    self.assertEqual(message[0:15], u'[\\HKCU\\Windows\\')

    event_object = tagged_event_objects[2]
    self.assertEqual(event_object.tag.comment, u'This is interesting')
    self.assertEqual(event_object.tag.labels[0], u'Malware')
    self.assertEqual(event_object.tag.labels[1], u'Benign')

    self.assertEqual(event_object.parser, u'UNKNOWN')

    # Test the newly added fourth tag, which should include data from
    # the first version as well.
    event_object = tagged_event_objects[3]
    self.assertEqual(event_object.tag.labels[0], u'Interesting')
    self.assertEqual(event_object.tag.labels[1], u'Malware')

  def testHasReports(self):
    """Tests the HasReports function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    self.assertFalse(storage_file.HasReports())

    storage_file.Close()

  def testHasTagging(self):
    """Tests the HasTagging function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    self.assertFalse(storage_file.HasTagging())

    storage_file.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = zip_file.StorageFile(temp_file, read_only=True)

      self.assertTrue(storage_file.HasTagging())

      storage_file.Close()

  def testSetEnableProfiling(self):
    """Tests the SetEnableProfiling function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      storage_file = zip_file.StorageFile(temp_file)

      storage_file.SetEnableProfiling(True)

      storage_file.Close()

      profiling_data_file = u'serializers-Storage.csv'
      if os.path.exists(profiling_data_file):
        os.remove(profiling_data_file)

  # TODO: add test for StoreReport

  def testStoreTagging(self):
    """Tests the StoreTagging function."""
    test_event_objects = test_lib.CreateTestEventObjects()
    test_event_tags = self._CreateTestEventTags()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      storage_file = zip_file.StorageFile(temp_file)

      for test_event_object in test_event_objects:
        storage_file.AddEventObject(test_event_object)

      storage_file.StoreTagging(test_event_tags[:-1])
      storage_file.StoreTagging(test_event_tags[-1:])

      storage_file.Close()

  def testWritePreprocessObject(self):
    """Tests the WritePreprocessObject function."""
    preprocessing_object = event.PreprocessObject()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      storage_file = zip_file.StorageFile(temp_file)

      storage_file.WritePreprocessObject(preprocessing_object)

      storage_file.Close()

  # TODO: move the functionality of this test to other more specific tests.
  def testStorage(self):
    """Test the storage object."""
    event_objects = []
    timestamps = []
    same_events = []

    serializer = protobuf_serializer.ProtobufEventObjectSerializer

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = zip_file.StorageFile(temp_file, read_only=True)

      for event_object in self._GetEventObjects(storage_file, 1):
        event_objects.append(event_object)
        timestamps.append(event_object.timestamp)
        if event_object.data_type == 'windows:registry:key_value':
          self.assertEqual(
              event_object.timestamp_desc,
              eventdata.EventTimestamp.WRITTEN_TIME)
        else:
          self.assertEqual(
              event_object.timestamp_desc,
              eventdata.EventTimestamp.WRITTEN_TIME)

      # Read the same events that were put in the group, just to compare
      # against.
      event_object = storage_file._GetEventObject(1, entry_index=1)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

      event_object = storage_file._GetEventObject(1, entry_index=2)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

      storage_file.Close()

    self.assertEqual(len(event_objects), 4)

    expected_timestamps = [
        1238934459000000, 1334940286000000, 1334961526929596, 1335966206929596]
    self.assertEqual(timestamps, expected_timestamps)


class ZIPStorageFileReaderTest(test_lib.StorageTestCase):
  """Tests for the ZIP-based storage file reader object."""

  def testGetEvents(self):
    """Tests the GetEvents function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    with zip_file.ZIPStorageFileReader(storage_file) as storage_reader:
      for event_object in storage_reader.GetEvents():
        timestamps.append(event_object.timestamp)

    expected_timestamps = [
        1343166324000000, 1344270407000000, 1390377153000000, 1390377153000000,
        1390377181000000, 1390377241000000, 1390377241000000, 1390377272000000,
        1392438730000000, 1418925272000000, 1427151678000000, 1427151678000123,
        1451584472000000, 1479431720000000, 1479431743000000]

    self.assertEqual(sorted(timestamps), expected_timestamps)

    # Test lower bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2014-02-16 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2030-12-31 23:59:59'))

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    with zip_file.ZIPStorageFileReader(storage_file) as storage_reader:
      for event_object in storage_reader.GetEvents(
          time_range=test_time_range):
        timestamps.append(event_object.timestamp)

    expected_timestamps = [
        1418925272000000,
        1427151678000000,
        1427151678000123,
        1451584472000000,
        1479431720000000,
        1479431743000000]

    self.assertEqual(sorted(timestamps), expected_timestamps)

    # Test upper bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2000-01-01 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2014-02-16 00:00:00'))

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    with zip_file.ZIPStorageFileReader(storage_file) as storage_reader:
      for event_object in storage_reader.GetEvents(
          time_range=test_time_range):
        timestamps.append(event_object.timestamp)

    expected_timestamps = [
        1343166324000000,
        1344270407000000,
        1390377153000000,
        1390377153000000,
        1390377181000000,
        1390377241000000,
        1390377241000000,
        1390377272000000,
        1392438730000000]

    self.assertEqual(sorted(timestamps), expected_timestamps)


class ZIPStorageFileWriterTest(unittest.TestCase):
  """Tests for the ZIP-based storage file writer object."""

  def testStorageWriter(self):
    """Test the storage writer."""
    test_event_objects = test_lib.CreateTestEventObjects()

    # The storage writer is normally run in a separate thread.
    # For the purpose of this test it has to be run in sequence,
    # hence the call to WriteEventObjects after all the event objects
    # have been queued up.

    # TODO: add upper queue limit.
    # A timeout is used to prevent the multi processing queue to close and
    # stop blocking the current process.
    test_queue = multi_process.MultiProcessingQueue(timeout=0.1)
    test_queue_producer = queue.ItemQueueProducer(test_queue)
    test_queue_producer.ProduceItems(test_event_objects)

    test_queue_producer.SignalAbort()

    preprocessing_object = event.PreprocessObject()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      storage_writer = zip_file.ZIPStorageFileWriter(
          test_queue, temp_file, preprocessing_object)
      storage_writer.WriteEventObjects()

      storage_file = zipfile.ZipFile(
          temp_file, mode='r', compression=zipfile.ZIP_DEFLATED)

      expected_filename_list = [
          u'information.dump', u'plaso_index.000001', u'plaso_meta.000001',
          u'plaso_proto.000001', u'plaso_timestamps.000001', u'serializer.txt']

      filename_list = sorted(storage_file.namelist())
      self.assertEqual(len(filename_list), 6)
      self.assertEqual(filename_list, expected_filename_list)


if __name__ == '__main__':
  unittest.main()
