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
from plaso.lib import eventdata
from plaso.parsers import winreg

container = event.EventContainer()


class TestRegistryFormatter(winreg.WinRegistryGenericFormatter):
  """A simple formatter for registry data."""

  ID_RE = re.compile('.+(Registry|UNKNOWN):', re.DOTALL)


class TestTextFormatter(eventdata.PlasoFormatter):
  """A simple formatter for registry data."""

  ID_RE = re.compile('None:(Some|Weird)', re.DOTALL)

  FORMAT_STRING = u'{text}'


class TestEvent(event.EventObject):
  """A test EventObject, contains minimum configuration."""

  def __init__(self):
    """Construct the test event."""
    super(TestEvent, self).__init__()
    self.source_short = 'TLOG'
    self.testkey = 'This is a test key.'


class FailEvent(event.EventObject):
  """An EventObject that does not define anything."""


class PlasoEventUnitTest(unittest.TestCase):
  """The unit test for plaso storage."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    container.hostname = 'MYHOSTNAME'

    container_a = event.EventContainer()
    container_b = event.EventContainer()

    container_a.username = 'joesmith'
    container_a.filename = 'c:/Users/joesmith/NTUSER.DAT'
    container_a.source_long = 'NTUSER.DAT Registry'

    container_b.filename = 'c:/Temp/evil.exe'
    container_b.source_long = 'Weird Log File'

    event_1 = event.RegistryEvent(
        u'MY AutoRun key', {u'Run': u'c:/Temp/evil.exe'}, 1334961526929596)
    event_1.source_long = 'UNKNOWN'
    event_2 = event.RegistryEvent(
        u'//HKCU/Secret/EvilEmpire/Malicious_key',
        {u'Value': u'send all the exes to the other world'}, 1334966206929596)
    event_2.source_long = 'UNKNOWN'
    event_3 = event.RegistryEvent(
        u'//HKCU/Windows/Normal', {u'Value': u'run all the benign stuff'},
        1334940286000000)
    event_3.source_long = 'UNKNOWN'

    event_4 = TestEvent()
    event_5 = TestEvent()
    event_6 = TestEvent()

    event_7 = event.TextEvent(1338934459000000,
                              ('This is a line by someone not reading the log'
                               ' line properly. And since this log line exceed'
                               's the accepted 80 chars it will be '
                               'shortened.'), 'Some random text file',
                              'nomachine', 'johndoe')
    event_7.text = event_7.body

    event_4.text = 'This log line reads ohh so much.'
    event_4.timestamp = 1335781787929596

    event_5.text = 'Nothing of interest here, move on.'
    event_5.timestamp = 1335781787929596

    event_6.text = 'Mr. Evil just logged into the machine and got root.'
    event_6.timestamp = 1335791207939596

    container_a.Append(event_1)
    container_a.Append(event_2)
    container_a.Append(event_3)

    container_b.Append(event_4)
    container_b.Append(event_5)
    container_b.Append(event_6)
    container_b.Append(event_7)

    container.Append(container_a)
    container.Append(container_b)

  def GetCSVLine(self, e):
    """Takes an EventObject and prints out a simple CSV line from it."""
    try:
      msg, _ = eventdata.GetMessageStrings(e)
    except KeyError:
      print e.attributes
      print e.__dict__
    return '%s,%s,%s,%s' % (e.timestamp,
                            e.source_short,
                            e.source_long,
                            msg)

  def testAllCount(self):
    """Test if we have all the events inside the container."""
    self.assertEquals(len(container), 7)

  def testAttributes(self):
    """Test if we can read the event attributes correctly."""
    events = {}
    for e in container:
      events[self.GetCSVLine(e)] = True

    self.assertIn(
        u'1334961526929596,REG,UNKNOWN,[MY AutoRun key] Run: c:/Temp/evil.exe',
        events)
    self.assertIn(
        (u'1334966206929596,REG,UNKNOWN,[//HKCU/Secret/EvilEmpire/Malicious_ke'
         'y] Value: send all the exes to the other world'), events)
    self.assertIn((u'1334940286000000,REG,UNKNOWN,[//HKCU/Windows'
                   '/Normal] Value: run all the benign stuff'), events)
    self.assertIn(('1335781787929596,TLOG,Weird Log File,This log line reads '
                   'ohh so much.'), events)
    self.assertIn(('1335781787929596,TLOG,Weird Log File,Nothing of interest'
                   ' here, move on.'), events)
    self.assertIn(('1335791207939596,TLOG,Weird Log File,Mr. Evil just logged'
                   ' into the machine and got root.'), events)

  def testContainerTimestamps(self):
    """Test first/last timestamps of containers."""

    self.assertEquals(container.first_timestamp, 1334940286000000)
    self.assertEquals(container.last_timestamp, 1338934459000000)

    first_array = []
    last_array = []
    for c in container.containers:
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
    events = list(container)

    self.assertRaises(AttributeError, getattr, events[0], 'doesnotexist')

  def testExistsInEventObject(self):
    """Calls to an attribute that is stored within the EventObject itself."""
    events = list(container)

    self.assertEquals(events[0].keyname, '//HKCU/Windows/Normal')

  def testExistsInParentObject(self):
    """Call to an attribute that is contained within the parent object."""
    events = list(container)

    self.assertEquals(events[0].filename, 'c:/Users/joesmith/NTUSER.DAT')

  def testNotInEventAndNoParent(self):
    """Call to an attribute that does not exist and no parent container ."""
    event = TestEvent()

    self.assertRaises(AttributeError, getattr, event, 'doesnotexist')

  def testFailEvent(self):
    """Calls to format_string_short that has not been defined."""
    e = FailEvent()
    self.assertRaises(AttributeError, getattr, e, 'format_string_short')

  def testFailAddContainerEvent(self):
    """Add an EventContainer that is isn't an EventContainer."""
    self.assertRaises(errors.NotAnEventContainerOrObject,
                      container.Append, 'asd')
    self.assertRaises(errors.NotAnEventContainerOrObject,
                      container.Append, FailEvent())

  def testTextBasedEvent(self):
    """Test a text based event."""
    for e in container:
      if e.source_short == 'LOG':
        msg, msg_short = eventdata.GetMessageStrings(e)
        self.assertEquals(msg, (
            'This is a line by someone not reading the log line properly. An'
            'd since this log line exceeds the accepted 80 chars it will be '
            'shortened.'))
        self.assertEquals(msg_short, (
            'This is a line by someone not reading the log line properl'
            'y. And since this l...'))

  def testGetAttributes(self):
    """Test the GetAttributes function."""
    # get the last event
    for e in container:
      my_event = e

    attr = my_event.GetAttributes()

    self.assertEquals(len(attr), 9)

    self.assertEquals(sorted(attr), ['body', 'filename', 'hostname',
                                     'source_long', 'source_short', 'text',
                                     'timestamp', 'timestamp_desc', 'username'])

if __name__ == '__main__':
  unittest.main()
