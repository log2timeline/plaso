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
"""This file contains the unit tests for the storage mechanism of Plaso."""
import os
import tempfile
import unittest
import zipfile

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.formatters import winreg

__pychecker__ = 'no-funcdoc'


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


class PlasoStorageUnitTest(unittest.TestCase):
  """The unit test for plaso storage."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.events = []

    event_1 = event.WinRegistryEvent(
        u'MY AutoRun key', {u'Value': u'c:/Temp/evil.exe'}, 13349615269295969)
    event_1.parser = 'UNKNOWN'

    event_2 = event.WinRegistryEvent(
        u'\\HKCU\\Secret\\EvilEmpire\\Malicious_key',
        {u'Value': u'send all the exes to the other world'}, 13359662069295961)
    event_2.parser = 'UNKNOWN'

    event_3 = event.WinRegistryEvent(
        u'\\HKCU\\Windows\\Normal', {u'Value': u'run all the benign stuff'},
        13349402860000000)
    event_3.parser = 'UNKNOWN'

    text_dict = {'text': (
        'This is a line by someone not reading the log line properly. And '
        'since this log line exceeds the accepted 80 chars it will be '
        'shortened.'), 'hostname': 'nomachine', 'username': 'johndoe'}
    event_4 = event.TextEvent(12389344590000000, text_dict)
    event_4.parser = 'UNKNOWN'

    self.events.append(event_1)
    self.events.append(event_2)
    self.events.append(event_3)
    self.events.append(event_4)

  def testSetStoreLimit(self):
    """Test the store limit options."""

  def testGetTimeBounds(self):
    """Test the time bound calls."""

  def testGetSortedEntry(self):
    """Test reading entries in the correct time order from the storage file."""

  def testStorageDumper(self):
    """Test the storage dumper."""
    self.assertEquals(len(self.events), 4)

    with tempfile.NamedTemporaryFile() as fh:
      # The dumper is normally run in another thread, but for the purpose
      # of this test it is run in sequence, hence the call to .Run() after
      # all has been queued up.
      dumper = storage.SimpleStorageDumper(fh)
      for e in self.events:
        serial = e.ToProtoString()
        dumper.AddEvent(serial)
      dumper.Close()
      dumper.Run()

      z_file = zipfile.ZipFile(fh, 'r', zipfile.ZIP_DEFLATED)
      self.assertEquals(len(z_file.namelist()), 3)

      self.assertEquals(sorted(z_file.namelist()), [
          'plaso_index.000001', 'plaso_meta.000001', 'plaso_proto.000001'])

  def testStorage(self):
    """Test the storage object."""
    evts = []
    timestamps = []
    group_mock = GroupMock()
    tags = []
    tags_mock = []
    groups = []
    group_events = []
    same_events = []

    with tempfile.NamedTemporaryFile() as fh:
      store = storage.PlasoStorage(fh)

      for event_object in self.events:
        serial = event_object.ToProtoString()
        store.AddEntry(serial)

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
      tag_2.tags = ('Malware',)
      tag_2.color = 'red'
      tags_mock.append(tag_2)

      tag_3 = event.EventTag()
      tag_3.store_number = 1
      tag_3.store_index = 2
      tag_3.comment = 'This is interesting'
      tag_3.tags = ('Malware', 'Benign')
      tag_3.color = 'red'
      tags_mock.append(tag_3)

      store.StoreTagging(tags_mock)

      group_mock.AddGroup(
          'Malicious', [(1, 1), (1, 2)], desc='Events that are malicious',
          color='red', first=13349402860000000, last=13349615269295969,
          cat='Malware')
      store.StoreGrouping(group_mock)
      store.CloseStorage()

      read_store = storage.PlasoStorage(fh, True)

      self.assertTrue(read_store.HasTagging())
      self.assertTrue(read_store.HasGrouping())

      for evt in read_store.GetEntries(1):
        evts.append(evt)
        timestamps.append(evt.timestamp)
        if evt.data_type == 'windows:registry:key_value':
          self.assertEquals(evt.timestamp_desc, 'Last Written')
        else:
          self.assertEquals(evt.timestamp_desc, 'Entry Written')

      for tag in read_store.GetTagging():
        evt = read_store.GetTaggedEvent(tag)
        tags.append(evt)

      groups = list(read_store.GetGrouping())
      self.assertEquals(len(groups), 1)
      group_events = list(read_store.GetEventsFromGroup(groups[0]))

      # Read the same events that were put in the group, just to compare
      # against.
      same_events.append(read_store.GetEntry(1, 1).ToProtoString())
      same_events.append(read_store.GetEntry(1, 2).ToProtoString())

    self.assertEquals(len(evts), 4)
    self.assertEquals(len(tags), 3)

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

    self.assertEquals(timestamps, [12389344590000000, 13349402860000000,
                                   13349615269295969, 13359662069295961])

    self.assertEquals(groups[0].name, u'Malicious')
    self.assertEquals(groups[0].category, u'Malware')
    self.assertEquals(groups[0].color, u'red')
    self.assertEquals(groups[0].description, u'Events that are malicious')
    self.assertEquals(groups[0].first_timestamp, 13349402860000000)
    self.assertEquals(groups[0].last_timestamp, 13349615269295969)

    self.assertEquals(len(group_events), 2)
    self.assertEquals(group_events[0].timestamp, 13349402860000000)
    self.assertEquals(group_events[1].timestamp, 13349615269295969L)

    self.assertEquals(same_events, list(a.ToProtoString() for a in
                                        group_events))


class StoreStorageTest(unittest.TestCase):
  """Test sorting storage file,"""

  def setUp(self):
    """Setup sets parameters that will be reused throughout this test."""
    # TODO: have sample output generated from the test.
    self.test_file = os.path.join('test_data', 'psort_test.out')
    self.first = 1342799054000000  # Fri, 20 Jul 2012 15:44:14 GMT
    self.last = 1342824552000000  # Fri, 20 Jul 2012 22:49:12 GMT

  def testStorageSort(self):
    """This test ensures that items read and output are in the correct order.

    This method by design outputs data as it runs. In order to test this a
    a modified output renderer is used for which the flush functionality has
    been removed.

    The test will be to read the TestEventBuffer storage and check to see
    if it matches the known good sort order.
    """

    store = storage.PlasoStorage(self.test_file, read_only=True)

    store.store_range = [2, 5]
    pfilter.TimeRangeCache.SetUpperTimestamp(self.last)
    pfilter.TimeRangeCache.SetLowerTimestamp(self.first)

    read_list = []
    event_object = store.GetSortedEntry()
    while event_object:
      read_list.append(event_object.timestamp)
      event_object = store.GetSortedEntry()

    correct_order = [1342799054000000L,
                     1342824253000000L,
                     1342824299000000L,
                     1342824546000000L,
                     1342824546000000L,
                     1342824552000000L,
                     1342824552000000L,
                     1342824552000000L]

    self.assertEquals(read_list, correct_order)


if __name__ == '__main__':
  unittest.main()
