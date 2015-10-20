#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the event storage."""

import os
import unittest
import zipfile

from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.formatters import winreg   # pylint: disable=unused-import
from plaso.serializer import protobuf_serializer
from plaso.storage import filters
from plaso.storage import zip_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class DummyObject(object):
  """Dummy object."""


class GroupMock(object):
  """Mock a class for grouping events together."""

  def __init__(self):
    """Initializes the mock group object."""
    self.groups = []

  def AddGroup(
      self, name, events, desc=None, first=0, last=0, color=None, cat=None):
    """Add a new group of events."""
    self.groups.append((name, events, desc, first, last, color, cat))

  def __iter__(self):
    """Iterator."""
    for name, events, desc, first, last, color, cat in self.groups:
      dummy = DummyObject()
      dummy.name = name
      dummy.events = events
      if desc:
        dummy.description = desc
      if first:
        dummy.first_timestamp = int(first)
      if last:
        dummy.last_timestamp = int(last)
      if color:
        dummy.color = color
      if cat:
        dummy.category = cat

      yield dummy


class SerializedDataStream(test_lib.StorageTestCase):
  """Tests for the serialized data stream object."""

  def testReadAndSeek(self):
    """Tests the ReadEntry and SeekEntryAtOffset functions."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_proto.000003'
    data_stream = zip_file._SerializedDataStream(zip_file_object, stream_name)

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
    data_stream = zip_file._SerializedDataStream(zip_file_object, stream_name)

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

  def testGetSerializedEventObjectStream(self):
    """Tests the _GetSerializedEventObjectStream function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    data_stream = storage_file._GetSerializedEventObjectStream(3)
    self.assertIsNotNone(data_stream)

  def testGetSerializedEventObjectStreamNumbers(self):
    """Tests the _GetSerializedEventObjectStreamNumbers function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    stream_numbers = storage_file._GetSerializedEventObjectStreamNumbers()
    self.assertEqual(len(stream_numbers), 7)

  def testGetSerializedEventObjectTimestampTable(self):
    """Tests the _GetSerializedEventObjectTimestampTable function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamp_table = storage_file._GetSerializedEventObjectTimestampTable(3)
    self.assertIsNotNone(timestamp_table)

  def testGetStreamNames(self):
    """Tests the _GetStreamNames function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    stream_names = list(storage_file._GetStreamNames())
    self.assertEqual(len(stream_names), 29)

  def testHasStream(self):
    """Tests the _HasStream function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    self.assertTrue(storage_file._HasStream(u'plaso_timestamps.000003'))
    self.assertFalse(storage_file._HasStream(u'bogus'))

  # TODO: add _OpenStream test.
  # TODO: add _ReadStream test.
  # TODO: add _WriteStream test.


class StorageFileTest(test_lib.StorageTestCase):
  """Tests for the ZIP storage file object."""

  def _CreateStorageFile(self, path):
    """Creates a storage file for testing.

    Args:
      path: a string containing the path of the storage file.

    Returns:
      A storage file object (instance of StorageFile).
    """
    test_event_objects = test_lib.CreateTestEventObjects()

    storage_file = zip_file.StorageFile(path)
    storage_file.AddEventObjects(test_event_objects)

    tags_mock = []

    # Add tagging.
    tag_1 = event.EventTag()
    tag_1.store_index = 0
    tag_1.store_number = 1
    tag_1.comment = u'My comment'
    tag_1.color = u'blue'
    tags_mock.append(tag_1)

    tag_2 = event.EventTag()
    tag_2.store_index = 1
    tag_2.store_number = 1
    tag_2.tags = [u'Malware']
    tag_2.color = u'red'
    tags_mock.append(tag_2)

    tag_3 = event.EventTag()
    tag_3.store_number = 1
    tag_3.store_index = 2
    tag_3.comment = u'This is interesting'
    tag_3.tags = [u'Malware', u'Benign']
    tag_3.color = u'red'
    tags_mock.append(tag_3)

    storage_file.StoreTagging(tags_mock)

    # Add additional tagging, second round.
    tag_4 = event.EventTag()
    tag_4.store_index = 1
    tag_4.store_number = 1
    tag_4.tags = [u'Interesting']

    storage_file.StoreTagging([tag_4])

    group_mock = GroupMock()
    group_mock.AddGroup(
        u'Malicious', [(1, 1), (1, 2)], desc=u'Events that are malicious',
        color=u'red', first=1334940286000000, last=1334961526929596,
        cat=u'Malware')
    storage_file.StoreGrouping(group_mock)
    storage_file.Close()

  def testGetStorageInformation(self):
    """Tests the GetStorageInformation function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    storage_information = storage_file.GetStorageInformation()
    self.assertEqual(len(storage_information), 1)

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

  def testGetSortedEntries(self):
    """Tests the GetSortedEntries function."""
    test_file = self._GetTestFilePath([u'psort_test.proto.plaso'])

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    for event_object in storage_file.GetSortedEntries():
      timestamps.append(event_object.timestamp)

    expected_timestamps = [
        1343166324000000, 1344270407000000, 1390377153000000, 1390377153000000,
        1390377181000000, 1390377241000000, 1390377241000000, 1390377272000000,
        1392438730000000, 1418925272000000, 1427151678000000, 1427151678000123,
        1451584472000000, 1479431720000000, 1479431743000000]

    self.assertEqual(sorted(timestamps), expected_timestamps)

    # Test lower bound time range filter.
    time_range_filter = filters.TimeRangeFilter(
        timelib.Timestamp.CopyFromString(u'2014-02-16 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2030-12-31 23:59:59'))

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    for event_object in storage_file.GetSortedEntries(
        time_range_filter=time_range_filter):
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
    time_range_filter = filters.TimeRangeFilter(
        timelib.Timestamp.CopyFromString(u'2000-01-01 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2014-02-16 00:00:00'))

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    for event_object in storage_file.GetSortedEntries(
        time_range_filter=time_range_filter):
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

  def testStorage(self):
    """Test the storage object."""
    formatter_mediator = formatters_mediator.FormatterMediator()

    event_objects = []
    tagged_event_objects = []
    timestamps = []
    groups = []
    group_events = []
    same_events = []

    serializer = protobuf_serializer.ProtobufEventObjectSerializer

    with shared_test_lib.TempDirectory() as dirname:
      temp_file = os.path.join(dirname, u'plaso.db')
      self._CreateStorageFile(temp_file)

      read_store = zip_file.StorageFile(temp_file, read_only=True)

      self.assertTrue(read_store.HasTagging())
      self.assertTrue(read_store.HasGrouping())

      for event_object in self._GetEventObjects(read_store, 1):
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

      for tag in read_store.GetTagging():
        event_object = self._GetTaggedEvent(read_store, tag)
        tagged_event_objects.append(event_object)

      groups = list(read_store.GetGrouping())
      self.assertEqual(len(groups), 1)
      group_events = self._GetEventsFromGroup(read_store, groups[0])

      # Read the same events that were put in the group, just to compare
      # against.
      event_object = read_store._GetEventObject(1, entry_index=1)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

      event_object = read_store._GetEventObject(1, entry_index=2)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

    self.assertEqual(len(event_objects), 4)
    self.assertEqual(len(tagged_event_objects), 4)

    event_object = tagged_event_objects[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-04-05 12:27:39')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.store_number, 1)
    self.assertEqual(event_object.store_index, 0)
    self.assertEqual(event_object.tag.comment, u'My comment')
    self.assertEqual(event_object.tag.color, u'blue')

    msg, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)
    self.assertEqual(msg[0:10], u'This is a ')

    event_object = tagged_event_objects[1]
    self.assertEqual(event_object.tag.tags[0], u'Malware')
    msg, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)
    self.assertEqual(msg[0:15], u'[\\HKCU\\Windows\\')

    event_object = tagged_event_objects[2]
    self.assertEqual(event_object.tag.comment, u'This is interesting')
    self.assertEqual(event_object.tag.tags[0], u'Malware')
    self.assertEqual(event_object.tag.tags[1], u'Benign')

    self.assertEqual(event_object.parser, u'UNKNOWN')

    event_object = tagged_event_objects[3]
    # Test the newly added fourth tag, which should include data from
    # the first version as well.
    self.assertEqual(event_object.tag.tags[0], u'Interesting')
    self.assertEqual(event_object.tag.tags[1], u'Malware')

    expected_timestamps = [
        1238934459000000, 1334940286000000, 1334961526929596, 1335966206929596]
    self.assertEqual(timestamps, expected_timestamps)

    self.assertEqual(groups[0].name, u'Malicious')
    self.assertEqual(groups[0].category, u'Malware')
    self.assertEqual(groups[0].color, u'red')
    self.assertEqual(groups[0].description, u'Events that are malicious')
    self.assertEqual(groups[0].first_timestamp, 1334940286000000)
    self.assertEqual(groups[0].last_timestamp, 1334961526929596)

    self.assertEqual(len(group_events), 2)
    self.assertEqual(group_events[0].timestamp, 1334940286000000)
    self.assertEqual(group_events[1].timestamp, 1334961526929596)

    proto_group_events = []
    for group_event in group_events:
      serialized_event_object = serializer.WriteSerialized(group_event)
      proto_group_events.append(serialized_event_object)

    self.assertEqual(same_events, proto_group_events)

  # TODO: add test for StoreReport.


if __name__ == '__main__':
  unittest.main()
