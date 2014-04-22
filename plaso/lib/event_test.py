#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""This file contains a unit test for the EventObject and EventContainer.

This is an implementation of an unit test for EventObject and EventContainer
storage mechanism for plaso.

The test consists of creating three EventContainers, and 6 EventObjects.

There is one base container. It contains the two other containers, and
they store the EventObjects.

The tests involve:
 + Read attributes, both set in the container level and event object.
 + Read in all the first/last timestamps of containers.

Error handling. The following tests are performed for error handling:
 + Access attributes that are not set.
"""

import unittest

from plaso.lib import errors
from plaso.lib import event


class TestEvent1(event.EventObject):
  """A test event object."""
  DATA_TYPE = 'test:event1'

  def __init__(self, timestamp, attributes):
    """Initializes the test event object."""
    super(TestEvent1, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = 'Some time in the future'
    self.attributes.update(attributes)


class FailEvent(event.EventObject):
  """An test event object without the minimal required initialization."""


class TestEventContainer(event.EventContainer):
  """A test event container."""

  def __init__(self):
    """Initializes the test event container."""
    super(TestEventContainer, self).__init__()

    self.hostname = 'MYHOSTNAME'

    # A sub event container that contains 3 event objects.
    container = event.EventContainer()
    container.username = 'joesmith'
    container.filename = 'c:/Users/joesmith/NTUSER.DAT'

    event_object = event.WinRegistryEvent(
        u'MY AutoRun key', {u'Run': u'c:/Temp/evil.exe'},
        timestamp=1334961526929596)
    container.Append(event_object)

    event_object = event.WinRegistryEvent(
        u'//HKCU/Secret/EvilEmpire/Malicious_key',
        {u'Value': u'REGALERT: send all the exes to the other world'},
        timestamp=1334966206929596)
    container.Append(event_object)

    event_object = event.WinRegistryEvent(
        u'//HKCU/Windows/Normal', {u'Value': u'run all the benign stuff'},
        timestamp=1334940286000000)
    container.Append(event_object)

    self.Append(container)

    # A sub event container that contains 4 event objects.
    container = event.EventContainer()
    container.filename = 'c:/Temp/evil.exe'

    container.Append(TestEvent1(1335781787929596, {
        'text': 'This log line reads ohh so much.'}))

    container.Append(TestEvent1(1335781787929596, {
        'text': 'Nothing of interest here, move on.'}))

    container.Append(TestEvent1(1335791207939596, {
        'text': 'Mr. Evil just logged into the machine and got root.'}))

    text_dict = {'body': (
        'This is a line by someone not reading the log line properly. And '
        'since this log line exceeds the accepted 80 chars it will be '
        'shortened.'), 'hostname': 'nomachine', 'username': 'johndoe'}
    event_object = event.TextEvent(1338934459000000, text_dict)
    event_object.text = event_object.body
    container.Append(event_object)

    self.Append(container)


class EventContainerTest(unittest.TestCase):
  """Tests for the event container object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._container = TestEventContainer()

  def testAllCount(self):
    """Test if we have all the events inside the container."""
    self.assertEquals(len(self._container), 7)

  def testContainerTimestamps(self):
    """Test first/last timestamps of containers."""
    self.assertEquals(
        self._container.first_timestamp, 1334940286000000)
    self.assertEquals(
        self._container.last_timestamp, 1338934459000000)

    # The container should have two sub containers:
    #   One with three events.
    #   One with four events.
    self.assertEquals(len(self._container), 7)
    self.assertEquals(len(self._container.containers), 2)
    # The parent container set one attribute, the hostname.
    self.assertEquals(len(self._container.attributes), 1)
    self.assertTrue('hostname' in self._container.attributes)
    self.assertEquals(len(self._container.containers[0].attributes), 2)

    first_array = []
    last_array = []
    for c in self._container.containers:
      first_array.append(c.first_timestamp)
      last_array.append(c.last_timestamp)

    first = set(first_array)
    last = set(last_array)

    self.assertIn(1334966206929596, last)
    self.assertIn(1334940286000000, first)
    self.assertIn(1335781787929596, first)
    self.assertIn(1338934459000000, last)
    self.assertIn(1334940286000000, first)
    self.assertIn(1334966206929596, last)
    self.assertIn(1335781787929596, first)
    self.assertIn(1338934459000000, last)
    self.assertIn(1334940286000000, first)
    self.assertIn(1334966206929596, last)
    self.assertIn(1335781787929596, first)
    self.assertIn(1338934459000000, last)

  def testDoesNotExist(self):
    """Calls to a non-existing attribute should result in an exception."""
    events = list(self._container)

    with self.assertRaises(AttributeError):
      getattr(events[0], 'doesnotexist')

  def testExistsInEventObject(self):
    """Calls to an attribute that is stored within the EventObject itself."""
    events = list(self._container.GetSortedEvents())

    self.assertEquals(events[0].keyname, '//HKCU/Windows/Normal')

  def testExistsRegalert(self):
    """Calls to the attribute that stores the regalert."""
    events = list(self._container.GetSortedEvents())

    self.assertEquals(events[2].regalert, True)

  def testExistsInParentObject(self):
    """Call to an attribute that is contained within the parent object."""
    events = list(self._container.GetSortedEvents())

    self.assertEquals(events[0].filename, 'c:/Users/joesmith/NTUSER.DAT')

  def testFailAddContainerEvent(self):
    """Add an EventContainer that is isn't an EventContainer."""
    with self.assertRaises(errors.NotAnEventContainerOrObject):
      self._container.Append('asd')

    with self.assertRaises(errors.NotAnEventContainerOrObject):
      self._container.Append(FailEvent())

  def testGetAttributes(self):
    """Test the GetAttributes function."""
    # TODO: clean up this code construction, retrieving the last event object
    # in the container can be done in a cleaner way.
    for event_object in self._container:
      last_event_object = event_object

    attr = last_event_object.GetAttributes()

    self.assertEquals(len(attr), 9)

    self.assertEquals(sorted(attr), [
        'body', 'data_type', 'filename', 'hostname', 'text', 'timestamp',
        'timestamp_desc', 'username', 'uuid'])


class EventObjectTest(unittest.TestCase):
  """Tests for the event object."""

  def testSameEvent(self):
    """Test the EventObject comparison."""
    event_a = event.EventObject()
    event_b = event.EventObject()
    event_c = event.EventObject()
    event_d = event.EventObject()
    event_e = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = u'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.inode = 124
    event_a.filename = u'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False
    event_a.metadata = {
        u'author': u'Some Random Dude',
        u'version': 1245L,
        u'last_changed': u'Long time ago'}
    event_a.strings = [
        u'This ', u'is a ', u'long string']

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.inode = 124
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False
    event_b.metadata = {
        'author': 'Some Random Dude',
        'version': 1245L,
        'last_changed': 'Long time ago'}
    event_b.strings = [
        'This ', 'is a ', 'long string']

    event_c.timestamp = 123
    event_c.timestamp_desc = 'LAST UPDATED'
    event_c.data_type = 'mock:nothing'
    event_c.inode = 124
    event_c.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_c.another_attribute = False

    event_d.timestamp = 14523
    event_d.timestamp_desc = 'LAST WRITTEN'
    event_d.data_type = 'mock:nothing'
    event_d.inode = 124
    event_d.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_d.another_attribute = False

    event_e.timestamp = 123
    event_e.timestamp_desc = 'LAST WRITTEN'
    event_e.data_type = 'mock:nothing'
    event_e.inode = 623423
    event_e.filename = 'c:/afrit/onnurskra.txt'
    event_e.another_attribute = False
    event_e.metadata = {
        'author': 'Some Random Dude',
        'version': 1245,
        'last_changed': 'Long time ago'}
    event_e.strings = [
        'This ', 'is a ', 'long string']

    self.assertEquals(event_a, event_b)
    self.assertNotEquals(event_a, event_c)
    self.assertEquals(event_a, event_e)
    self.assertNotEquals(event_c, event_d)

  def testEqualityString(self):
    """Test the EventObject EqualityString."""
    event_a = event.EventObject()
    event_b = event.EventObject()
    event_c = event.EventObject()
    event_d = event.EventObject()
    event_e = event.EventObject()
    event_f = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = 'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.inode = 124
    event_a.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.inode = 124
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    event_c.timestamp = 123
    event_c.timestamp_desc = 'LAST UPDATED'
    event_c.data_type = 'mock:nothing'
    event_c.inode = 124
    event_c.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_c.another_attribute = False

    event_d.timestamp = 14523
    event_d.timestamp_desc = 'LAST WRITTEN'
    event_d.data_type = 'mock:nothing'
    event_d.inode = 124
    event_d.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_d.another_attribute = False

    event_e.timestamp = 123
    event_e.timestamp_desc = 'LAST WRITTEN'
    event_e.data_type = 'mock:nothing'
    event_e.inode = 623423
    event_e.filename = 'c:/afrit/öñṅûŗ₅ḱŖūα.txt'
    event_e.another_attribute = False

    event_f.timestamp = 14523
    event_f.timestamp_desc = 'LAST WRITTEN'
    event_f.data_type = 'mock:nothing'
    event_f.inode = 124
    event_f.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_f.another_attribute = False
    event_f.weirdness = 'I am a potato'

    self.assertEquals(event_a.EqualityString(), event_b.EqualityString())
    self.assertNotEquals(event_a.EqualityString(), event_c.EqualityString())
    self.assertEquals(event_a.EqualityString(), event_e.EqualityString())
    self.assertNotEquals(event_c.EqualityString(), event_d.EqualityString())
    self.assertNotEquals(event_d.EqualityString(), event_f.EqualityString())

  def testEqualityPfileStatParserMissingInode(self):
    """Test that PfileStatParser files with missing inodes are distinct"""
    event_a = event.EventObject()
    event_b = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = 'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.parser = 'PfileStatParser'
    event_a.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.parser = 'PfileStatParser'
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    self.assertNotEquals(event_a, event_b)

  def testEqualityStringPfileStatParserMissingInode(self):
    """Test that PfileStatParser files with missing inodes are distinct"""
    event_a = event.EventObject()
    event_b = event.EventObject()

    event_a.timestamp = 123
    event_a.timestamp_desc = 'LAST WRITTEN'
    event_a.data_type = 'mock:nothing'
    event_a.parser = 'PfileStatParser'
    event_a.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_a.another_attribute = False

    event_b.timestamp = 123
    event_b.timestamp_desc = 'LAST WRITTEN'
    event_b.data_type = 'mock:nothing'
    event_b.parser = 'PfileStatParser'
    event_b.filename = 'c:/bull/skrytinmappa/skra.txt'
    event_b.another_attribute = False

    self.assertNotEquals(event_a.EqualityString(), event_b.EqualityString())

  def testNotInEventAndNoParent(self):
    """Call to an attribute that does not exist and no parent container ."""
    event_object = TestEvent1(0, {})

    with self.assertRaises(AttributeError):
      getattr(event_object, 'doesnotexist')

  def testFailEvent(self):
    """Calls to format_string_short that has not been defined."""
    e = FailEvent()

    with self.assertRaises(AttributeError):
      getattr(e, 'format_string_short')


if __name__ == '__main__':
  unittest.main()
