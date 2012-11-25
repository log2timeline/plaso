#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
import tempfile
import unittest
import zipfile

from plaso.lib import event
from plaso.lib import storage
from plaso.proto import plaso_storage_pb2

__pychecker__ = 'no-funcdoc'


class DummyObject(object):
  """Dummy object."""


class TagMock(object):
  """Mock a class for tagging events."""

  def __init__(self):
    self.items = []

  def AddEntry(self, store_number=1, store_index=0, comment=None, tag=None,
               color=None):
    self.items.append((store_number, store_index, comment, tag, color))

  def __iter__(self):
    for nr, index, cmt, tag, color in self.items:
      dummy = DummyObject()
      dummy.store_number = nr
      dummy.store_index = index
      if cmt:
        dummy.comment = cmt
      if tag:
        dummy.tag = tag
      if color:
        dummy.color = color
      yield dummy


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

    event_1 = event.RegistryEvent(
        u'MY AutoRun key', {u'Value': u'c:/Temp/evil.exe'}, 13349615269295969)
    event_1.source_long = 'NTUSER.DAT Registry File'
    event_1.parser = 'UNKNOWN'

    event_2 = event.RegistryEvent(
        u'\\HKCU\\Secret\\EvilEmpire\\Malicious_key',
        {u'Value': u'send all the exes to the other world'}, 13359662069295961)
    event_2.source_long = 'NTUSER.DAT Registry File'
    event_2.parser = 'UNKNOWN'

    event_3 = event.RegistryEvent(
        u'\\HKCU\\Windows\\Normal', {u'Value': u'run all the benign stuff'},
        13349402860000000)
    event_3.source_long = 'NTUSER.DAT Registry File'
    event_3.parser = 'UNKNOWN'

    event_4 = event.TextEvent(12389344590000000,
                              ('This is a line by someone not reading the log'
                               ' line properly. And since this log line exceed'
                               's the accepted 80 chars it will be '
                               'shortened.'), 'Some random text file',
                              'nomachine', 'johndoe')
    event_4.parser = 'UNKNOWN'

    self.events.append(event_1)
    self.events.append(event_2)
    self.events.append(event_3)
    self.events.append(event_4)

  def testStorageDumper(self):
    """Test the storage dumper."""
    self.assertEquals(len(self.events), 4)

    with tempfile.NamedTemporaryFile() as fh:
      # The dumper is normally run in another thread, but for the purpose
      # of this test it is run in sequence, hence the call to .Run() after
      # all has been queued up.
      dumper = storage.SimpleStorageDumper(fh)
      for e in self.events:
        serial = storage.PlasoStorage.SerializeEvent(e)
        dumper.AddEvent(serial)
      dumper.Close()
      dumper.Run()

      z_file = zipfile.ZipFile(fh, 'r', zipfile.ZIP_DEFLATED)
      self.assertEquals(len(z_file.namelist()), 3)

      self.assertEquals(sorted(z_file.namelist()), ['plaso_index.000001',
                                                    'plaso_meta.000001',
                                                    'plaso_proto.000001'])

  def testStorage(self):
    """Test the storage object."""
    protos = []
    timestamps = []
    tag_mock = TagMock()
    group_mock = GroupMock()
    tags = []
    groups = []
    group_events = []
    same_events = []

    with tempfile.NamedTemporaryFile() as fh:
      store = storage.PlasoStorage(fh)

      for my_event in self.events:
        serial = storage.PlasoStorage.SerializeEvent(my_event)
        store.AddEntry(serial)

      # Add tagging.
      tag_mock.AddEntry(store_index=0, comment='My comment', color='blue')
      tag_mock.AddEntry(store_index=1, tag='Malware', color='red')
      tag_mock.AddEntry(store_index=2, comment='This is interesting',
                        tag='Malware', color='red')

      store.StoreTagging(tag_mock)

      group_mock.AddGroup(
          'Malicious', [(1, 1), (1, 2)], desc='Events that are malicious',
          color='red', first=13349402860000000, last=13349615269295969,
          cat='Malware')
      store.StoreGrouping(group_mock)
      store.CloseStorage()

      read_store = storage.PlasoStorage(fh, True)

      self.assertTrue(read_store.HasTagging())
      self.assertTrue(read_store.HasGrouping())

      for proto in read_store.GetEntries(1):
        protos.append(proto)
        timestamps.append(proto.timestamp)
        if proto.source_short == plaso_storage_pb2.EventObject.REG:
          self.assertEquals(proto.source_long, 'NTUSER.DAT Registry File')
          self.assertEquals(proto.timestamp_desc, 'Last Written')
        else:
          self.assertEquals(proto.source_long, 'Some random text file')
          self.assertEquals(proto.timestamp_desc, 'Entry Written')

      for tag in read_store.GetTagging():
        proto = read_store.GetTaggedEvent(tag)
        tags.append(proto)

      groups = list(read_store.GetGrouping())
      self.assertEquals(len(groups), 1)
      group_events = list(read_store.GetEventsFromGroup(groups[0]))

      # Read the same events that were put in the group, just to compare
      # against.
      same_events.append(read_store.GetEntry(1, 1))
      same_events.append(read_store.GetEntry(1, 2))

    self.assertEquals(len(protos), 4)
    self.assertEquals(len(tags), 3)

    self.assertEquals(tags[0].timestamp, 12389344590000000)
    self.assertEquals(tags[0].store_number, 1)
    self.assertEquals(tags[0].store_index, 0)
    self.assertEquals(tags[0].tag.comment, u'My comment')
    self.assertEquals(tags[0].tag.color, u'blue')
    self.assertEquals(tags[0].description_long[0:10], u'This is a ')

    self.assertEquals(tags[1].tag.tag, 'Malware')
    self.assertEquals(tags[1].description_long[0:15], u'[\\HKCU\\Windows\\')

    self.assertEquals(tags[2].tag.comment, u'This is interesting')
    self.assertEquals(tags[2].tag.tag, 'Malware')

    attributes = dict((a.key, a.value) for a in tags[2].attributes)
    self.assertEquals(attributes['parser'], 'UNKNOWN')

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
    self.assertEquals(group_events[0].source_long, u'NTUSER.DAT Registry File')
    self.assertEquals(group_events[1].timestamp, 13349615269295969L)

    self.assertEquals(same_events, group_events)


if __name__ == '__main__':
  unittest.main()
