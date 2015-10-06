#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the event storage."""

import os
import unittest

from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.lib import timelib
from plaso.formatters import winreg   # pylint: disable=unused-import
from plaso.serializer import protobuf_serializer

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


class StorageFileTest(unittest.TestCase):
  """Tests for the plaso storage file."""

  def testStorage(self):
    """Test the storage object."""
    test_event_objects = test_lib.CreateTestEventObjects()
    formatter_mediator = formatters_mediator.FormatterMediator()

    event_objects = []
    timestamps = []
    group_mock = GroupMock()
    tags = []
    tags_mock = []
    groups = []
    group_events = []
    same_events = []

    serializer = protobuf_serializer.ProtobufEventObjectSerializer

    with shared_test_lib.TempDirectory() as dirname:
      temp_file = os.path.join(dirname, 'plaso.db')
      store = storage.StorageFile(temp_file)
      store.AddEventObjects(test_event_objects)

      # Add tagging.
      tag_1 = event.EventTag()
      tag_1.store_index = 0
      tag_1.store_number = 1
      tag_1.comment = 'My comment'
      tag_1.color = 'blue'
      tags_mock.append(tag_1)

      tag_2 = event.EventTag()
      tag_2.store_index = 1
      tag_2.store_number = 1
      tag_2.tags = ['Malware']
      tag_2.color = 'red'
      tags_mock.append(tag_2)

      tag_3 = event.EventTag()
      tag_3.store_number = 1
      tag_3.store_index = 2
      tag_3.comment = 'This is interesting'
      tag_3.tags = ['Malware', 'Benign']
      tag_3.color = 'red'
      tags_mock.append(tag_3)

      store.StoreTagging(tags_mock)

      # Add additional tagging, second round.
      tag_4 = event.EventTag()
      tag_4.store_index = 1
      tag_4.store_number = 1
      tag_4.tags = ['Interesting']

      store.StoreTagging([tag_4])

      group_mock.AddGroup(
          'Malicious', [(1, 1), (1, 2)], desc='Events that are malicious',
          color='red', first=1334940286000000, last=1334961526929596,
          cat='Malware')
      store.StoreGrouping(group_mock)
      store.Close()

      read_store = storage.StorageFile(temp_file, read_only=True)

      self.assertTrue(read_store.HasTagging())
      self.assertTrue(read_store.HasGrouping())

      for event_object in read_store.GetEntries(1):
        event_objects.append(event_object)
        timestamps.append(event_object.timestamp)
        if event_object.data_type == 'windows:registry:key_value':
          self.assertEqual(event_object.timestamp_desc,
                           eventdata.EventTimestamp.WRITTEN_TIME)
        else:
          self.assertEqual(event_object.timestamp_desc,
                           eventdata.EventTimestamp.WRITTEN_TIME)

      for tag in read_store.GetTagging():
        event_object = read_store.GetTaggedEvent(tag)
        tags.append(event_object)

      groups = list(read_store.GetGrouping())
      self.assertEqual(len(groups), 1)
      group_events = list(read_store.GetEventsFromGroup(groups[0]))

      # Read the same events that were put in the group, just to compare
      # against.
      event_object = read_store.GetEventObject(1, 1)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

      event_object = read_store.GetEventObject(1, 2)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

    self.assertEqual(len(event_objects), 4)
    self.assertEqual(len(tags), 4)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-04-05 12:27:39')
    self.assertEqual(tags[0].timestamp, expected_timestamp)
    self.assertEqual(tags[0].store_number, 1)
    self.assertEqual(tags[0].store_index, 0)
    self.assertEqual(tags[0].tag.comment, u'My comment')
    self.assertEqual(tags[0].tag.color, u'blue')

    msg, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, tags[0])
    self.assertEqual(msg[0:10], u'This is a ')

    self.assertEqual(tags[1].tag.tags[0], 'Malware')
    msg, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, tags[1])
    self.assertEqual(msg[0:15], u'[\\HKCU\\Windows\\')

    self.assertEqual(tags[2].tag.comment, u'This is interesting')
    self.assertEqual(tags[2].tag.tags[0], 'Malware')
    self.assertEqual(tags[2].tag.tags[1], 'Benign')

    self.assertEqual(tags[2].parser, 'UNKNOWN')

    # Test the newly added fourth tag, which should include data from
    # the first version as well.
    self.assertEqual(tags[3].tag.tags[0], 'Interesting')
    self.assertEqual(tags[3].tag.tags[1], 'Malware')

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

  def testStorageSort(self):
    """This test ensures that items read and output are in the expected order.

    This method by design outputs data as it runs. In order to test this a
    a modified output renderer is used for which the flush functionality has
    been removed.

    The test will be to read the TestEventBuffer storage and check to see
    if it matches the known good sort order.
    """
    # TODO: have sample output generated from the test.
    # TODO: Use input data with a defined year.  syslog parser chooses a
    # year based on system clock; forcing updates to test file if regenerated.
    test_file = os.path.join(u'test_data', u'psort_test.proto.plaso')
    first = timelib.Timestamp.CopyFromString(u'2012-07-20 15:44:14')
    last = timelib.Timestamp.CopyFromString(u'2016-11-18 01:15:43')

    pfilter.TimeRangeCache.ResetTimeConstraints()
    pfilter.TimeRangeCache.SetUpperTimestamp(last)
    pfilter.TimeRangeCache.SetLowerTimestamp(first)
    store = storage.StorageFile(test_file, read_only=True)

    store.store_range = [1, 5, 6]

    read_list = []
    event_object = store.GetSortedEntry()
    while event_object:
      read_list.append(event_object.timestamp)
      event_object = store.GetSortedEntry()

    expected_timestamps = [
        1344270407000000, 1392438730000000, 1427151678000000, 1451584472000000]

    self.assertEqual(read_list, expected_timestamps)


if __name__ == '__main__':
  unittest.main()
