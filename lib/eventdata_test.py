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
"""This file contains a unit test for the EventFilter."""
import re
import unittest

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import event_test
from plaso.lib import eventdata
from plaso.formatters import winreg


class TestEvent1Formatter(eventdata.EventFormatter):
  """Test event 1 formatter."""
  DATA_TYPE = 'test:event1'
  FORMAT_STRING = u'{text}'


class WrongEventFormatter(eventdata.EventFormatter):
  """A simple event formatter."""
  DATA_TYPE = 'test:wrong'
  FORMAT_STRING = u'This format string does not match {body}.'


class EventFormatterUnitTest(unittest.TestCase):
  """The unit test for the event formatter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.container = event_test.TestEventContainer()

  def GetCSVLine(self, event_object):
    """Takes an EventObject and prints out a simple CSV line from it."""
    try:
      msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event_object)
    except KeyError:
      print event_object.attributes
      print event_object.__dict__
    return '%s,%s,%s,%s' % (
        event_object.timestamp, event_object.source_short,
        event_object.source_long, msg)

  def testInitialization(self):
    """Test the initialization."""
    self.assertTrue(TestEvent1Formatter())

  def testAttributes(self):
    """Test if we can read the event attributes correctly."""
    events = {}
    for event_object in self.container:
      events[self.GetCSVLine(event_object)] = True

    self.assertIn(
        u'1334961526929596,REG,UNKNOWN,[MY AutoRun key] Run: c:/Temp/evil.exe',
        events)
    self.assertIn(
        (u'1334966206929596,REG,UNKNOWN,[//HKCU/Secret/EvilEmpire/Malicious_ke'
         'y] Value: REGALERT: send all the exes to the other world'), events)
    self.assertIn((u'1334940286000000,REG,UNKNOWN,[//HKCU/Windows'
                   '/Normal] Value: run all the benign stuff'), events)
    self.assertIn(('1335781787929596,FILE,Weird Log File,This log line reads '
                   'ohh so much.'), events)
    self.assertIn(('1335781787929596,FILE,Weird Log File,Nothing of interest'
                   ' here, move on.'), events)
    self.assertIn(('1335791207939596,FILE,Weird Log File,Mr. Evil just logged'
                   ' into the machine and got root.'), events)

  def testTextBasedEvent(self):
    """Test a text based event."""
    for event_object in self.container:
      if event_object.source_short == 'LOG':
        msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
            event_object)

        self.assertEquals(msg, (
            'This is a line by someone not reading the log line properly. And '
            'since this log line exceeds the accepted 80 chars it will be '
            'shortened.'))
        self.assertEquals(msg_short, (
            'This is a line by someone not reading the log line properly. '
            'And since this l...'))


class ConditionalTestEvent1(event_test.TestEvent1):
  DATA_TYPE = 'test:conditional_event1'


class ConditionalTestEvent1Formatter(eventdata.ConditionalEventFormatter):
  """Test event 1 conditional (event) formatter."""
  DATA_TYPE = 'test:conditional_event1'
  FORMAT_STRING_PIECES = [u'Description: {description}',
                          u'Comment',
                          u'Value: 0x{numeric:02x}',
                          u'Optional: {optional}',
                          u'Text: {text}']


class BrokenConditionalEventFormatter(eventdata.ConditionalEventFormatter):
  """A broken conditional event formatter."""
  DATA_TYPE = 'test:broken_conditional'
  FORMAT_STRING_PIECES = [u'{too} {many} formatting placeholders']


class ConditionalEventFormatterUnitTest(unittest.TestCase):
  """The unit test for the conditional event formatter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.event_object = ConditionalTestEvent1(1335791207939596, {
        'numeric': 12, 'description': 'this is beyond words',
        'text': 'but we\'re still trying to say something about the event'})

  def testInitialization(self):
    """Test the initialization."""
    self.assertTrue(ConditionalTestEvent1Formatter())
    with self.assertRaises(RuntimeError):
        BrokenConditionalEventFormatter()

  def testGetMessages(self):
    """Test get messages."""
    event_formatter = ConditionalTestEvent1Formatter()
    msg, _ = event_formatter.GetMessages(self.event_object)

    expected_msg = (u'Description: this is beyond words Comment Value: 0x0c '
                    u'Text: but we\'re still trying to say something about '
                    u'the event')
    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
