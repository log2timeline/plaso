#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the event storage."""

import os
import unittest
import uuid
import zipfile

from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import definitions
from plaso.lib import event
from plaso.lib import timelib
from plaso.formatters import winreg   # pylint: disable=unused-import
from plaso.storage import time_range
from plaso.storage import zip_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class SerializedDataStream(shared_test_lib.BaseTestCase):
  """Tests for the serialized data stream object."""

  # pylint: disable=protected-access

  def testReadAndSeek(self):
    """Tests the ReadEntry and SeekEntryAtOffset functions."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_proto.000002'
    data_stream = zip_file._SerializedDataStream(
        zip_file_object, test_file, stream_name)

    # The plaso_index.000002 stream contains 3 protobuf serialized
    # event objects. The first one at offset 0 of size 762 (including the
    # 4 bytes of the entry size) and the second one at offset 762 of size 742.
    self.assertEqual(data_stream.entry_index, 0)

    entry_data1 = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 1)
    self.assertEqual(data_stream._stream_offset, 762)
    self.assertIsNotNone(entry_data1)

    entry_data2 = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 2)
    self.assertEqual(data_stream._stream_offset, 1504)
    self.assertIsNotNone(entry_data2)

    # Read more entries than in the stream.
    for _ in range(3, 18):
      entry_data = data_stream.ReadEntry()

    self.assertEqual(data_stream.entry_index, 16)
    self.assertEqual(data_stream._stream_offset, 11605)
    self.assertIsNone(entry_data)

    data_stream.SeekEntryAtOffset(1, 762)
    entry_data = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 2)
    self.assertEqual(data_stream._stream_offset, 1504)
    self.assertEqual(entry_data, entry_data2)

    data_stream.SeekEntryAtOffset(0, 0)
    entry_data = data_stream.ReadEntry()
    self.assertEqual(data_stream.entry_index, 1)
    self.assertEqual(data_stream._stream_offset, 762)
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


class SerializedDataOffsetTable(shared_test_lib.BaseTestCase):
  """Tests for the serialized data offset table object."""

  # pylint: disable=protected-access

  def testGetOffset(self):
    """Tests the GetOffset function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_index.000002'
    offset_table = zip_file._SerializedDataOffsetTable(
        zip_file_object, stream_name)
    offset_table.Read()

    self.assertEqual(offset_table.GetOffset(0), 0)
    self.assertEqual(offset_table.GetOffset(1), 762)

    with self.assertRaises(IndexError):
      offset_table.GetOffset(99)

    self.assertEqual(offset_table.GetOffset(-1), 10902)
    self.assertEqual(offset_table.GetOffset(-2), 10110)

    with self.assertRaises(IndexError):
      offset_table.GetOffset(-99)

  def testRead(self):
    """Tests the Read function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_index.000002'
    offset_table = zip_file._SerializedDataOffsetTable(
        zip_file_object, stream_name)
    offset_table.Read()

    stream_name = u'bogus'
    offset_table = zip_file._SerializedDataOffsetTable(
        zip_file_object, stream_name)

    with self.assertRaises(IOError):
      offset_table.Read()


class SerializedDataTimestampTable(shared_test_lib.BaseTestCase):
  """Tests for the serialized data offset table object."""

  # pylint: disable=protected-access

  def testGetTimestamp(self):
    """Tests the GetTimestamp function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_timestamps.000002'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)
    offset_table.Read()

    self.assertEqual(offset_table.GetTimestamp(0), 1453449153000000)
    self.assertEqual(offset_table.GetTimestamp(1), 1453449153000000)

    with self.assertRaises(IndexError):
      offset_table.GetTimestamp(99)

    self.assertEqual(offset_table.GetTimestamp(-1), 1542503743000000)
    self.assertEqual(offset_table.GetTimestamp(-2), 1542503720000000)

    with self.assertRaises(IndexError):
      offset_table.GetTimestamp(-99)

  def testRead(self):
    """Tests the Read function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    zip_file_object = zipfile.ZipFile(
        test_file, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)

    stream_name = u'plaso_timestamps.000002'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)
    offset_table.Read()

    stream_name = u'bogus'
    offset_table = zip_file._SerializedDataTimestampTable(
        zip_file_object, stream_name)

    with self.assertRaises(IOError):
      offset_table.Read()


class ZIPStorageFileTest(shared_test_lib.BaseTestCase):
  """Tests for the ZIP-based storage file object."""

  # pylint: disable=protected-access

  def _CreateTestEventTags(self):
    """Creates the event tags for testing.

    Returns:
      A list of event tags (instances of EventTag).
    """
    event_tags = []

    event_tag = events.EventTag()
    event_tag.store_index = 0
    event_tag.store_number = 1
    event_tag.comment = u'My comment'
    event_tags.append(event_tag)

    event_tag = events.EventTag()
    event_tag.store_index = 1
    event_tag.store_number = 1
    event_tag.AddLabel(u'Malware')
    event_tags.append(event_tag)

    event_tag = events.EventTag()
    event_tag.store_number = 1
    event_tag.store_index = 2
    event_tag.comment = u'This is interesting'
    event_tag.AddLabels([u'Malware', u'Benign'])
    event_tags.append(event_tag)

    event_tag = events.EventTag()
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
    event_objects = test_lib.CreateTestEventObjects()
    event_tags = self._CreateTestEventTags()

    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(path, read_only=False)
    for event_object in event_objects:
      storage_file.AddEvent(event_object)

    storage_file.AddEventTags(event_tags[:-1])
    storage_file.AddEventTags(event_tags[-1:])

    storage_file.Close()

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

  # TODO: add test for _BuildTagIndex.
  # TODO: add test for _GetEventObject.
  # TODO: add test for _GetEventObjectSerializedData.
  # TODO: add test for _GetEventSource.
  # TODO: add test for _GetEventSourceSerializedData.
  # TODO: add test for _GetEventTagIndexValue.
  # TODO: add test for _GetLastStreamNumber.
  # TODO: add test for _InitializeMergeBuffer.

  # The _GetSerializedDataStream function is tested by the
  # _GetSerializedEventOffsetTable and _GetSerializedEventSourceOffsetTable
  # tests.

  # TODO: add test for _GetSerializedDataOffsetTable.
  # TODO: add test for _GetSerializedDataStreamNumbers.

  def testGetSerializedEventOffsetTable(self):
    """Tests the _GetSerializedEventOffsetTable function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    offset_table = storage_file._GetSerializedEventOffsetTable(2)
    self.assertIsNotNone(offset_table)

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventOffsetTable(99)

    storage_file.Close()

  def testGetSerializedEventSourceOffsetTable(self):
    """Tests the _GetSerializedEventSourceOffsetTable function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    # TODO: add positive test.

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventSourceOffsetTable(99)

    storage_file.Close()

  # The _GetSerializedDataStream function is tested by the
  # _GetSerializedEventSourceStream and _GetSerializedEventStream tests.

  def testGetSerializedEventSourceStream(self):
    """Tests the _GetSerializedEventSourceStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    # TODO: add positive test.

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventSourceStream(99)

    storage_file.Close()

  def testGetSerializedEventStream(self):
    """Tests the _GetSerializedEventStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    data_stream = storage_file._GetSerializedEventStream(2)
    self.assertIsNotNone(data_stream)

    with self.assertRaises(IOError):
      storage_file._GetSerializedEventStream(99)

    storage_file.Close()

  # The _GetSerializedDataStreamNumbers function is tested by the
  # _GetSerializedEventStreamNumbers and _GetSerializedEventSourceStreamNumbers
  # tests.

  def testGetSerializedEventSourceStreamNumbers(self):
    """Tests the _GetSerializedEventSourceStreamNumbers function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    stream_numbers = storage_file._GetSerializedEventSourceStreamNumbers()
    self.assertEqual(len(stream_numbers), 0)

    storage_file.Close()

  def testGetSerializedEventStreamNumbers(self):
    """Tests the _GetSerializedEventStreamNumbers function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    stream_numbers = storage_file._GetSerializedEventStreamNumbers()
    self.assertEqual(len(stream_numbers), 2)

    storage_file.Close()

  def testGetSerializedEventTimestampTable(self):
    """Tests the _GetSerializedEventTimestampTable function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    timestamp_table = storage_file._GetSerializedEventTimestampTable(2)
    self.assertIsNotNone(timestamp_table)

    storage_file.Close()

  def testGetStreamNames(self):
    """Tests the _GetStreamNames function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    stream_names = list(storage_file._GetStreamNames())
    self.assertEqual(len(stream_names), 11)

    storage_file.Close()

  def testHasStream(self):
    """Tests the _HasStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    self.assertTrue(storage_file._HasStream(u'plaso_timestamps.000002'))
    self.assertFalse(storage_file._HasStream(u'bogus'))

    storage_file.Close()

  # The _OpenRead function is tested by the open close test.

  def testOpenStream(self):
    """Tests the _OpenStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    file_object = storage_file._OpenStream(u'plaso_timestamps.000002')
    self.assertIsNotNone(file_object)

    file_object = storage_file._OpenStream(u'bogus')
    self.assertIsNone(file_object)

    storage_file.Close()

  # The _OpenWrite function is tested by the open close test.

  # The _OpenZIPFile function is tested by the open close test.

  # TODO: add test for _ReadAttributeContainer.
  # TODO: add test for _ReadAttributeContainerFromStreamEntry.
  # TODO: add test for _ReadAttributeContainersFromStream.
  # TODO: add test for _ReadEventTagByIdentifier.
  # TODO: add test for _ReadSerializerStream.
  # TODO: add test for _ReadStorageMetadata.

  def testReadStream(self):
    """Tests the _ReadStream function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    stream_data = storage_file._ReadStream(u'plaso_timestamps.000002')
    self.assertNotEqual(stream_data, b'')

    stream_data = storage_file._ReadStream(u'bogus')
    self.assertEqual(stream_data, b'')

    storage_file.Close()

  # TODO: add test for _WriteAttributeContainer.
  # TODO: add test for _WriteSerializedErrors.
  # TODO: add test for _WriteSerializedEvents.
  # TODO: add test for _WriteSerializedEventSources.
  # TODO: add test for _WriteSerializedEventTags.

  # The _WriteSessionStart and _WriteSessionCompletion functions at tested by
  # WriteSessionStart and WriteSessionCompletion.

  def testWriteStorageMetadata(self):
    """Tests the _WriteStorageMetadata function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      storage_file._WriteStorageMetadata()

      storage_file.Close()

  def testWriteStream(self):
    """Tests the _WriteStream function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      storage_file._WriteStream(u'bogus', b'test')

      storage_file.Close()

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file)

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
      storage_file.Open(temp_file, read_only=False)

      storage_file.AddAnalysisReport(analysis_report)

      storage_file.Close()

  def testAddError(self):
    """Tests the AddError function."""
    extraction_error = errors.ExtractionError(u'Test extraction error')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      storage_file.AddError(extraction_error)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddError.

  def testAddEvent(self):
    """Tests the AddEvent function."""
    event_objects = test_lib.CreateTestEventObjects()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      for event_object in event_objects:
        storage_file.AddEvent(event_object)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddEvent.

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      storage_file.AddEventSource(event_source)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddEventSource.

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    event_objects = test_lib.CreateTestEventObjects()
    event_tags = self._CreateTestEventTags()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      for event_object in event_objects:
        storage_file.AddEvent(event_object)

      for event_tag in event_tags:
        storage_file.AddEventTag(event_tag)

      storage_file.Close()

    # TODO: add test for exceeding buffer limit in AddEventTag.

  def testAddEventTags(self):
    """Tests the AddEventTags function."""
    event_objects = test_lib.CreateTestEventObjects()
    event_tags = self._CreateTestEventTags()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      for event_object in event_objects:
        storage_file.AddEvent(event_object)

      storage_file.AddEventTags(event_tags[:-1])
      storage_file.AddEventTags(event_tags[-1:])

      storage_file.Close()

  def testEnableAndDisableProfiling(self):
    """Tests the EnableProfiling and DisableProfiling function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      storage_file.EnableProfiling()
      storage_file.Close()
      storage_file.DisableProfiling()

      profiling_data_file = u'serializers-Storage.csv'
      if os.path.exists(profiling_data_file):
        os.remove(profiling_data_file)

  def testGetAnalysisReports(self):
    """Tests the GetAnalysisReports function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    analysis_reports = list(storage_file.GetAnalysisReports())
    self.assertEqual(len(analysis_reports), 2)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    analysis_reports = list(storage_file.GetAnalysisReports())
    self.assertEqual(len(analysis_reports), 0)

    storage_file.Close()

  def testGetErrors(self):
    """Tests the GetErrors function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    test_event_sources = list(storage_file.GetErrors())
    self.assertEqual(len(test_event_sources), 0)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    test_event_sources = list(storage_file.GetErrors())
    self.assertEqual(len(test_event_sources), 0)

    storage_file.Close()

  def testGetEventSources(self):
    """Tests the GetEventSources function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    test_event_sources = list(storage_file.GetEventSources())
    self.assertEqual(len(test_event_sources), 0)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    test_event_sources = list(storage_file.GetEventSources())
    self.assertEqual(len(test_event_sources), 0)

    storage_file.Close()

  # TODO: add test for GetEventSourcesCurrentSession.

  def testGetEventTags(self):
    """Tests the GetEventTags function."""
    formatter_mediator = formatters_mediator.FormatterMediator()

    tagged_events = []

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file)

      for event_tag in storage_file.GetEventTags():
        event_object = self._GetTaggedEvent(storage_file, event_tag)
        tagged_events.append(event_object)

      storage_file.Close()

    self.assertEqual(len(tagged_events), 4)

    event_object = tagged_events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-04-05 12:27:39')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.store_number, 1)
    self.assertEqual(event_object.store_index, 0)
    self.assertEqual(event_object.tag.comment, u'My comment')

    message, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)
    self.assertEqual(message[0:10], u'This is a ')

    event_object = tagged_events[1]
    self.assertEqual(event_object.tag.labels[0], u'Malware')
    message, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)
    self.assertEqual(message[0:14], u'[HKCU\\Windows\\')

    event_object = tagged_events[2]
    self.assertEqual(event_object.tag.comment, u'This is interesting')
    self.assertEqual(event_object.tag.labels[0], u'Malware')
    self.assertEqual(event_object.tag.labels[1], u'Benign')

    self.assertEqual(event_object.parser, u'UNKNOWN')

    # Test the newly added fourth tag, which should include data from
    # the first version as well.
    event_object = tagged_events[3]
    self.assertEqual(event_object.tag.labels[0], u'Interesting')
    self.assertEqual(event_object.tag.labels[1], u'Malware')

  # TODO: add test for GetSessions.

  def testGetSortedEntry(self):
    """Tests the GetSortedEntry function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    expected_timestamp = 1453449153000000

    event_object = storage_file.GetSortedEntry()
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Test lower bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'),
        timelib.Timestamp.CopyFromString(u'2030-12-31 23:59:59'))

    storage_file.Close()

    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    expected_timestamp = 1462105168000000

    event_object = storage_file.GetSortedEntry(time_range=test_time_range)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Test upper bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2000-01-01 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'))

    storage_file.Close()

    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    expected_timestamp = 1453449153000000

    event_object = storage_file.GetSortedEntry(time_range=test_time_range)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    storage_file.Close()

  def testHasAnalysisReports(self):
    """Tests the HasAnalysisReports function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    has_reports = storage_file.HasAnalysisReports()
    self.assertTrue(has_reports)

    storage_file.Close()

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    has_reports = storage_file.HasAnalysisReports()
    self.assertFalse(has_reports)

    storage_file.Close()

  def testHasEventTags(self):
    """Tests the HasEventTags function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)

    self.assertFalse(storage_file.HasEventTags())

    storage_file.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      self._CreateTestStorageFileWithTags(temp_file)

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file)

      self.assertTrue(storage_file.HasEventTags())

      storage_file.Close()

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    # Read-only of session storage.
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.ZIPStorageFile()
    storage_file.Open(test_file)
    storage_file.Close()

    # Write append of session storage.
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)
      storage_file.Close()

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)
      storage_file.Close()

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file)
      storage_file.Close()

    # Write append of task storage.
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(temp_file, read_only=False)
      storage_file.Close()

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)
      storage_file.Close()

      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file)
      storage_file.Close()

  def testWriteSessionStartAndCompletion(self):
    """Tests the WriteSessionStart and WriteSessionCompletion functions."""
    session_start = sessions.SessionStart()
    session_completion = sessions.SessionCompletion(session_start.identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      storage_file.WriteSessionStart(session_start)
      storage_file.WriteSessionCompletion(session_completion)

      storage_file.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(temp_file, read_only=False)

      with self.assertRaises(IOError):
        storage_file.WriteSessionStart(session_start)

      with self.assertRaises(IOError):
        storage_file.WriteSessionCompletion(session_completion)

      storage_file.Close()

  def testWriteTaskStartAndCompletion(self):
    """Tests the WriteTaskStart and WriteTaskCompletion functions."""
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    task_start = tasks.TaskStart(session_identifier)
    task_completion = tasks.TaskCompletion(
        task_start.identifier, session_identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(temp_file, read_only=False)

      storage_file.WriteTaskStart(task_start)
      storage_file.WriteTaskCompletion(task_completion)

      storage_file.Close()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.ZIPStorageFile()
      storage_file.Open(temp_file, read_only=False)

      with self.assertRaises(IOError):
        storage_file.WriteTaskStart(task_start)

      with self.assertRaises(IOError):
        storage_file.WriteTaskCompletion(task_completion)

      storage_file.Close()


# TODO: remove StorageFile.
class StorageFileTest(shared_test_lib.BaseTestCase):
  """Tests for the ZIP storage file object."""

  # pylint: disable=protected-access

  def testGetStorageInformation(self):
    """Tests the GetStorageInformation function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = zip_file.StorageFile(test_file, read_only=True)

    storage_information = storage_file.GetStorageInformation()
    self.assertEqual(len(storage_information), 2)

    storage_file.Close()

  def testWritePreprocessObject(self):
    """Tests the WritePreprocessObject function."""
    preprocess_object = event.PreprocessObject()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_file = zip_file.StorageFile(temp_file)

      storage_file.WritePreprocessObject(preprocess_object)

      storage_file.Close()


class ZIPStorageFileReaderTest(shared_test_lib.BaseTestCase):
  """Tests for the ZIP-based storage file reader object."""

  def testGetEvents(self):
    """Tests the GetEvents function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    with zip_file.ZIPStorageFileReader(storage_file) as storage_reader:
      for event_object in storage_reader.GetEvents():
        timestamps.append(event_object.timestamp)

    expected_timestamps = [
        1453449153000000, 1453449153000000, 1453449153000000, 1453449153000000,
        1453449181000000, 1453449181000000, 1453449241000000, 1453449241000000,
        1453449241000000, 1453449241000000, 1453449272000000, 1453449272000000,
        1456708543000000, 1456708543000000, 1462105168000000, 1462105168000000,
        1462105168000000, 1462105168000000, 1462105169000000, 1462105170000000,
        1482083672000000, 1482083672000000, 1490310078000000, 1490310078000000,
        1490310078000123, 1490310078000123, 1514742872000000, 1514742872000000,
        1542503720000000, 1542503720000000, 1542503743000000, 1542503743000000]

    self.assertEqual(len(timestamps), 32)
    self.assertEqual(sorted(timestamps), expected_timestamps)

    # Test lower bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'),
        timelib.Timestamp.CopyFromString(u'2030-12-31 23:59:59'))

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    with zip_file.ZIPStorageFileReader(storage_file) as storage_reader:
      for event_object in storage_reader.GetEvents(
          time_range=test_time_range):
        timestamps.append(event_object.timestamp)

    expected_timestamps = [
        1462105168000000, 1462105168000000, 1462105168000000, 1462105168000000,
        1462105169000000, 1462105170000000, 1482083672000000, 1482083672000000,
        1490310078000000, 1490310078000000, 1490310078000123, 1490310078000123,
        1514742872000000, 1514742872000000, 1542503720000000, 1542503720000000,
        1542503743000000, 1542503743000000]

    self.assertEqual(sorted(timestamps), expected_timestamps)

    # Test upper bound time range filter.
    test_time_range = time_range.TimeRange(
        timelib.Timestamp.CopyFromString(u'2000-01-01 00:00:00'),
        timelib.Timestamp.CopyFromString(u'2016-04-30 06:41:49'))

    storage_file = zip_file.StorageFile(test_file, read_only=True)

    timestamps = []
    with zip_file.ZIPStorageFileReader(storage_file) as storage_reader:
      for event_object in storage_reader.GetEvents(
          time_range=test_time_range):
        timestamps.append(event_object.timestamp)

    expected_timestamps = [
        1453449153000000, 1453449153000000, 1453449153000000, 1453449153000000,
        1453449181000000, 1453449181000000, 1453449241000000, 1453449241000000,
        1453449241000000, 1453449241000000, 1453449272000000, 1453449272000000,
        1456708543000000, 1456708543000000]

    self.assertEqual(sorted(timestamps), expected_timestamps)


class ZIPStorageFileWriterTest(shared_test_lib.BaseTestCase):
  """Tests for the ZIP-based storage file writer object."""

  # TODO: add test for AddAnalysisReport.
  # TODO: add test for AddEvent.
  # TODO: add test for AddEventSource.
  # TODO: add test for AddEventTag.
  # TODO: add test for Open/Close.
  # TODO: add test for GetEventSources.
  # TODO: add test for WriteSessionCompletion.
  # TODO: add test for WriteSessionStart.

  def testStorageWriter(self):
    """Test the storage writer."""
    event_objects = test_lib.CreateTestEventObjects()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = zip_file.ZIPStorageFileWriter(temp_file)

      storage_writer.Open()

      session_start = sessions.SessionStart()
      storage_writer.WriteSessionStart(session_start)

      for event_object in event_objects:
        storage_writer.AddEvent(event_object)

      preprocess_object = event.PreprocessObject()
      storage_writer.WritePreprocessObject(preprocess_object)

      storage_writer.WriteSessionCompletion()
      storage_writer.Close()

      storage_file = zipfile.ZipFile(
          temp_file, mode='r', compression=zipfile.ZIP_DEFLATED)

      expected_filename_list = sorted([
          u'event_data.000001',
          u'event_index.000001',
          u'event_timestamps.000001',
          u'information.dump',
          u'metadata.txt',
          u'session_completion.000001',
          u'session_start.000001'])

      filename_list = sorted(storage_file.namelist())
      self.assertEqual(len(filename_list), 7)
      self.assertEqual(filename_list, expected_filename_list)


if __name__ == '__main__':
  unittest.main()
