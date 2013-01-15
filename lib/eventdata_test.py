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
from plaso.parsers import winreg


class TestRegistryFormatter(winreg.WinRegistryGenericFormatter):
  """A simple formatter for registry data."""

  ID_RE = re.compile('.+(Registry|UNKNOWN):', re.DOTALL)


class TestTextFormatter(eventdata.TextFormatter):
  """A simple formatter for registry data."""

  ID_RE = re.compile('UNKNOWN:(Some|Weird)', re.DOTALL)

  FORMAT_STRING = u'{text}'


class PlasoEventUnitTest(unittest.TestCase):
  """The unit test for plaso storage."""

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
         'y] Value: send all the exes to the other world'), events)
    self.assertIn((u'1334940286000000,REG,UNKNOWN,[//HKCU/Windows'
                   '/Normal] Value: run all the benign stuff'), events)
    self.assertIn(('1335781787929596,TLOG,Weird Log File,This log line reads '
                   'ohh so much.'), events)
    self.assertIn(('1335781787929596,TLOG,Weird Log File,Nothing of interest'
                   ' here, move on.'), events)
    self.assertIn(('1335791207939596,TLOG,Weird Log File,Mr. Evil just logged'
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


if __name__ == '__main__':
  unittest.main()
