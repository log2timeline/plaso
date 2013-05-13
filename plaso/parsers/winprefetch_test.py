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
"""Tests for the Windows prefetch parser."""
import os
import unittest

from plaso.formatters import winprefetch
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import winprefetch


class WinPrefetchParserTest(unittest.TestCase):
  """Tests for the Windows prefetch parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = winprefetch.WinPrefetchParser(pre_obj)
    self.maxDiff = None

  def testParseFile(self):
    """Read a Prefetch file and run a few tests."""
    test_file = os.path.join('test_data', 'ping.pf')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    self.assertEquals(len(events), 2)

    # Date: 2012-04-06T19:00:55.932955+00:00.
    self.assertEquals(events[0].timestamp, 1333738855932955)
    self.assertEquals(events[0].timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)

    # Created timestamp.
    event_object = events[1]

    # Date: 2010-11-10T17:37:26.484375+00:00.
    self.assertEquals(event_object.timestamp, 1289410646484375)
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.LAST_RUNTIME)

    self.assertEquals(event_object.executable, u'PING.EXE')
    self.assertEquals(event_object.hash_value, u'0xB29F6629')
    self.assertEquals(event_object.path, (
        '\\WINDOWS\\SYSTEM32\\PING.EXE'))
    self.assertEquals(event_object.run_count, 14)
    self.assertEquals(event_object.volume_path, u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEquals(event_object.volume_serial, '0xAC036525')

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    # TODO: Before submit, fix this. For some reason the msg_short
    # does not get populated (despite being so in regular output).
    #self.assertEquals(msg_short, u'PING.EXE was run 14 time(s)')
    self.assertEquals(msg, (
        u'Superfetch [PING.EXE] was executed - run count 14 path:'
        ' \WINDOWS\SYSTEM32\PING.EXE [ vol serial: 0xAC036525 vol path:'
        ' \DEVICE\HARDDISKVOLUME1]'))


if __name__ == '__main__':
  unittest.main()
