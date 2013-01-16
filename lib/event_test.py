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
import re
import unittest

from plaso.lib import errors
from plaso.lib import event


class TestEvent(event.EventObject):
  """A test event object."""

  def __init__(self, timestamp, attributes):
    """Initializes the test event object."""
    super(TestEvent, self).__init__()
    self.timestamp = timestamp
    self.source_short = 'TEST'
    self.attributes.update(attributes)


class FailEvent(event.EventObject):
  """An test event object without the minimal required initialization."""


class TestEventContainer(event.EventContainer):
  def __init__(self):
    """Initializes the test event container."""
    super(TestEventContainer, self).__init__()

    self.hostname = 'MYHOSTNAME'

    # A sub event container that contains 3 event objects.
    container = event.EventContainer()
    container.username = 'joesmith'
    container.filename = 'c:/Users/joesmith/NTUSER.DAT'
    container.source_long = 'NTUSER.DAT Registry'

    event_object = event.RegistryEvent(
        u'MY AutoRun key', {u'Run': u'c:/Temp/evil.exe'}, 1334961526929596)
    event_object.source_long = 'UNKNOWN'
    container.Append(event_object)

    event_object = event.RegistryEvent(
        u'//HKCU/Secret/EvilEmpire/Malicious_key',
        {u'Value': u'send all the exes to the other world'}, 1334966206929596)
    event_object.source_long = 'UNKNOWN'
    container.Append(event_object)

    event_object = event.RegistryEvent(
        u'//HKCU/Windows/Normal', {u'Value': u'run all the benign stuff'},
        1334940286000000)
    event_object.source_long = 'UNKNOWN'
    container.Append(event_object)

    self.Append(container)

    # A sub event container that contains 4 event objects.
    container = event.EventContainer()
    container.filename = 'c:/Temp/evil.exe'
    container.source_long = 'Weird Log File'

    container.Append(TestEvent(1335781787929596, {
        'text': 'This log line reads ohh so much.'}))

    container.Append(TestEvent(1335781787929596, {
        'text': 'Nothing of interest here, move on.'}))

    container.Append(TestEvent(1335791207939596, {
        'text': 'Mr. Evil just logged into the machine and got root.'}))

    event_object = event.TextEvent(1338934459000000, (
        'This is a line by someone not reading the log line properly. And '
        'since this log line exceeds the accepted 80 chars it will be '
        'shortened.'), 'Some random text file', 'nomachine', 'johndoe')
    event_object.text = event_object.body
    container.Append(event_object)

    self.Append(container)


class PlasoEventUnitTest(unittest.TestCase):
  """The unit test for plaso storage."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.container = TestEventContainer()

  def testAllCount(self):
    """Test if we have all the events inside the container."""
    self.assertEquals(len(self.container), 7)

  def testContainerTimestamps(self):
    """Test first/last timestamps of containers."""

    self.assertEquals(self.container.first_timestamp, 1334940286000000)
    self.assertEquals(self.container.last_timestamp, 1338934459000000)

    first_array = []
    last_array = []
    for c in self.container.containers:
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
    events = list(self.container)

    self.assertRaises(AttributeError, getattr, events[0], 'doesnotexist')

  def testExistsInEventObject(self):
    """Calls to an attribute that is stored within the EventObject itself."""
    events = list(self.container)

    self.assertEquals(events[0].keyname, '//HKCU/Windows/Normal')

  def testExistsInParentObject(self):
    """Call to an attribute that is contained within the parent object."""
    events = list(self.container)

    self.assertEquals(events[0].filename, 'c:/Users/joesmith/NTUSER.DAT')

  def testNotInEventAndNoParent(self):
    """Call to an attribute that does not exist and no parent container ."""
    event = TestEvent(0, {})

    self.assertRaises(AttributeError, getattr, event, 'doesnotexist')

  def testFailEvent(self):
    """Calls to format_string_short that has not been defined."""
    e = FailEvent()
    self.assertRaises(AttributeError, getattr, e, 'format_string_short')

  def testFailAddContainerEvent(self):
    """Add an EventContainer that is isn't an EventContainer."""
    self.assertRaises(errors.NotAnEventContainerOrObject,
                      self.container.Append, 'asd')
    self.assertRaises(errors.NotAnEventContainerOrObject,
                      self.container.Append, FailEvent())

  def testGetAttributes(self):
    """Test the GetAttributes function."""
    # get the last event
    for e in self.container:
      my_event = e

    attr = my_event.GetAttributes()

    self.assertEquals(len(attr), 9)

    self.assertEquals(sorted(attr), [
        'body', 'filename', 'hostname', 'source_long', 'source_short', 'text',
        'timestamp', 'timestamp_desc', 'username'])

  def testSerialization(self):
    """Test serialize event and attribute saving."""
    evt = event.EventObject()
    evt.timestamp = 1234124
    evt.timestamp_desc = 'Written'
    evt.source_short = 'LOG'
    evt.source_long = 'Some Source Long'
    # Should not get stored.
    evt.empty_attribute = u''
    # Is stored.
    evt.zero_integer = 0
    evt.integer = 34
    evt.string = 'Normal string'
    evt.unicode_string = u'And I\'m a unicorn.'
    evt.my_list = ['asf', 4234, 2, 54, 'asf']
    evt.my_dict = {'a': 'not b', 'c': 34, 'list': ['sf', 234], 'an': [234, 32]}
    evt.a_tuple = ('some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35)
    # Should not get stored.
    evt.null_value = None

    proto = evt.ToProto()
    proto_ser = evt.ToProtoString()

    self.assertEquals(len(list(proto.attributes)), 7)
    evt_throw = event.EventObject()
    attributes = dict(
        evt_throw._AttributeFromProto(a) for a in proto.attributes)
    self.assertFalse('empty_attribute' in attributes)
    self.assertTrue('zero_integer' in attributes)
    self.assertEquals(len(attributes.get('my_list', [])), 5)
    self.assertEquals(attributes.get('string'), 'Normal string')
    self.assertEquals(len(attributes.get('a_tuple')), 4)

    # Go back
    evt2 = event.EventObject()
    evt2.FromProtoString(proto_ser)

    self.assertEquals(evt2.timestamp, evt.timestamp)
    self.assertEquals(evt2.source_short, evt.source_short)
    self.assertEquals(evt.my_dict, evt2.my_dict)
    self.assertEquals(evt.my_list, evt2.my_list)
    self.assertEquals(evt.string, evt2.string)
    self.assertFalse('empty_attribute' in evt2.attributes)


if __name__ == '__main__':
  unittest.main()
