#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the tests for the event storage."""

import os
import tempfile
import unittest
import zipfile

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import pfilter
from plaso.lib import queue
from plaso.lib import storage
from plaso.formatters import winreg   # pylint: disable-msg=unused-import
from plaso.serializer import protobuf_serializer


class DummyObject(object):
  """Dummy object."""


class GroupMock(object):
  """Mock a class for grouping events together."""
  def __init__(self):
    self.groups = []

  def AddGroup(self, name, events, desc=None, first=0, last=0, color=None,
               cat=None):
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

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._event_objects = []

    event_1 = event.WinRegistryEvent(
        u'MY AutoRun key', {u'Value': u'c:/Temp/evil.exe'},
        timestamp=13349615269295969)
    event_1.parser = 'UNKNOWN'

    event_2 = event.WinRegistryEvent(
        u'\\HKCU\\Secret\\EvilEmpire\\Malicious_key',
        {u'Value': u'send all the exes to the other world'},
        timestamp=13359662069295961)
    event_2.parser = 'UNKNOWN'

    event_3 = event.WinRegistryEvent(
        u'\\HKCU\\Windows\\Normal', {u'Value': u'run all the benign stuff'},
        timestamp=13349402860000000)
    event_3.parser = 'UNKNOWN'

    text_dict = {'text': (
        'This is a line by someone not reading the log line properly. And '
        'since this log line exceeds the accepted 80 chars it will be '
        'shortened.'), 'hostname': 'nomachine', 'username': 'johndoe'}
    event_4 = event.TextEvent(12389344590000000, text_dict)
    event_4.parser = 'UNKNOWN'

    self._event_objects.append(event_1)
    self._event_objects.append(event_2)
    self._event_objects.append(event_3)
    self._event_objects.append(event_4)

  def testStorageWriter(self):
    """Test the storage writer."""
    self.assertEquals(len(self._event_objects), 4)

    # The storage writer is normally run in a separate thread.
    # For the purpose of this test it has to be run in sequence,
    # hence the call to WriteEventObjects after all the event objects
    # have been queued up.
    test_queue = queue.MultiThreadedQueue()
    test_queue_producer = queue.EventObjectQueueProducer(test_queue)
    test_queue_producer.ProduceEventObjects(self._event_objects)
    test_queue_producer.SignalEndOfInput()

    with tempfile.NamedTemporaryFile() as temp_file:
      storage_writer = storage.StorageFileWriter(test_queue, temp_file)
      storage_writer.WriteEventObjects()

      z_file = zipfile.ZipFile(temp_file, 'r', zipfile.ZIP_DEFLATED)

      expected_z_filename_list = [
          'plaso_index.000001', 'plaso_meta.000001', 'plaso_proto.000001',
          'plaso_timestamps.000001']

      z_filename_list = sorted(z_file.namelist())
      self.assertEquals(len(z_filename_list), 4)
      self.assertEquals(z_filename_list, expected_z_filename_list)

  def testStorage(self):
    """Test the storage object."""
    event_objects = []
    timestamps = []
    group_mock = GroupMock()
    tags = []
    tags_mock = []
    groups = []
    group_events = []
    same_events = []

    serializer = protobuf_serializer.ProtobufEventObjectSerializer

    with tempfile.NamedTemporaryFile() as temp_file:
      store = storage.StorageFile(temp_file)
      store.AddEventObjects(self._event_objects)

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
          color='red', first=13349402860000000, last=13349615269295969,
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
          self.assertEquals(event_object.timestamp_desc, 'Last Written')
        else:
          self.assertEquals(event_object.timestamp_desc,
                            eventdata.EventTimestamp.WRITTEN_TIME)

      for tag in read_store.GetTagging():
        event_object = read_store.GetTaggedEvent(tag)
        tags.append(event_object)

      groups = list(read_store.GetGrouping())
      self.assertEquals(len(groups), 1)
      group_events = list(read_store.GetEventsFromGroup(groups[0]))

      # Read the same events that were put in the group, just to compare
      # against.
      event_object = read_store.GetEventObject(1, 1)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

      event_object = read_store.GetEventObject(1, 2)
      serialized_event_object = serializer.WriteSerialized(event_object)
      same_events.append(serialized_event_object)

    self.assertEquals(len(event_objects), 4)
    self.assertEquals(len(tags), 4)

    self.assertEquals(tags[0].timestamp, 12389344590000000)
    self.assertEquals(tags[0].store_number, 1)
    self.assertEquals(tags[0].store_index, 0)
    self.assertEquals(tags[0].tag.comment, u'My comment')
    self.assertEquals(tags[0].tag.color, u'blue')

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(tags[0])
    self.assertEquals(msg[0:10], u'This is a ')

    self.assertEquals(tags[1].tag.tags[0], 'Malware')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(tags[1])
    self.assertEquals(msg[0:15], u'[\\HKCU\\Windows\\')

    self.assertEquals(tags[2].tag.comment, u'This is interesting')
    self.assertEquals(tags[2].tag.tags[0], 'Malware')
    self.assertEquals(tags[2].tag.tags[1], 'Benign')

    self.assertEquals(tags[2].parser, 'UNKNOWN')

    # Test the newly added fourth tag, which should include data from
    # the first version as well.
    self.assertEquals(tags[3].tag.tags[0], 'Interesting')
    self.assertEquals(tags[3].tag.tags[1], 'Malware')

    expected_timestamps = [
        12389344590000000, 13349402860000000, 13349615269295969,
        13359662069295961]
    self.assertEquals(timestamps, expected_timestamps)

    self.assertEquals(groups[0].name, u'Malicious')
    self.assertEquals(groups[0].category, u'Malware')
    self.assertEquals(groups[0].color, u'red')
    self.assertEquals(groups[0].description, u'Events that are malicious')
    self.assertEquals(groups[0].first_timestamp, 13349402860000000)
    self.assertEquals(groups[0].last_timestamp, 13349615269295969)

    self.assertEquals(len(group_events), 2)
    self.assertEquals(group_events[0].timestamp, 13349402860000000)
    self.assertEquals(group_events[1].timestamp, 13349615269295969L)

    proto_group_events = []
    for group_event in group_events:
      serialized_event_object = serializer.WriteSerialized(group_event)
      proto_group_events.append(serialized_event_object)

    self.assertEquals(same_events, proto_group_events)


class StoreStorageTest(unittest.TestCase):
  """Test sorting storage file,"""

  def setUp(self):
    """Setup sets parameters that will be reused throughout this test."""
    # TODO: have sample output generated from the test.
    # TODO: Use input data with a defined year.  syslog parser chooses a
    # year based on system clock; forcing updates to test file if regenerated.
    self.test_file = os.path.join('test_data', 'psort_test.out')
    self.first = 1342799054000000  # 2012-07-20T15:44:14+00:00
    self.last = 1479431743000000 # 2016-11-18T01:15:43+00:00

  def testStorageSort(self):
    """This test ensures that items read and output are in the expected order.

    This method by design outputs data as it runs. In order to test this a
    a modified output renderer is used for which the flush functionality has
    been removed.

    The test will be to read the TestEventBuffer storage and check to see
    if it matches the known good sort order.
    """
    pfilter.TimeRangeCache.ResetTimeConstraints()
    pfilter.TimeRangeCache.SetUpperTimestamp(self.last)
    pfilter.TimeRangeCache.SetLowerTimestamp(self.first)
    store = storage.StorageFile(self.test_file, read_only=True)

    store.store_range = [1, 5, 6]

    read_list = []
    event_object = store.GetSortedEntry()
    while event_object:
      read_list.append(event_object.timestamp)
      event_object = store.GetSortedEntry()

    expected_timestamps = [
        1344270407000000L, 1392438730000000L, 1427151678000000L,
        1451584472000000L]

    self.assertEquals(read_list, expected_timestamps)


if __name__ == '__main__':
  unittest.main()
