#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Tests for the Windows prefetch parser."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winprefetch as winprefetch_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import test_lib
from plaso.parsers import winprefetch


class WinPrefetchParserTest(test_lib.ParserTestCase):
  """Tests for the Windows prefetch parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self._parser = winprefetch.WinPrefetchParser(pre_obj)
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testParse17(self):
    """Tests the Parse function on a version 17 Prefetch file."""
    test_file = os.path.join('test_data', 'CMD.EXE-087B4001.pf')
    events = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(events)

    # Check the number of events in event container.
    self.assertEquals(len(event_container.events), 2)
    self.assertEquals(event_container.version, 17)

    # The last run time.
    event_object = event_container.events[0]

    # date -u -d"Mar 10, 2013 10:11:49.281250000 UTC" +"%s.%N"
    # 1362910309.281250000
    self.assertEquals(event_object.timestamp, 1362910309281250)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)
    self.assertEquals(event_object.executable, u'CMD.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x087b4001)

    # The creation time.
    event_object = event_container.events[1]

    # date -u -d "Mar 10, 2013 10:19:46.234375000 UTC" +"%s.%N"
    # 1362910786.234375000
    self.assertEquals(event_object.timestamp, 1362910786234375)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

  def testParse23(self):
    """Tests the Parse function on a version 23 Prefetch file."""
    test_file = os.path.join('test_data', 'PING.EXE-B29F6629.pf')
    events = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(events)

    # Check the number of events in event container.
    self.assertEquals(len(event_container.events), 2)
    self.assertEquals(event_container.version, 23)

    # The last run time.
    event_object = event_container.events[0]

    # Date: 2012-04-06T19:00:55.932955+00:00.
    self.assertEquals(event_object.timestamp, 1333738855932955)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)

    # The creation time.
    event_object = event_container.events[1]

    # Date: 2010-11-10T17:37:26.484375+00:00.
    self.assertEquals(event_object.timestamp, 1289410646484375)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    self.assertEquals(event_object.executable, u'PING.EXE')
    self.assertEquals(event_object.prefetch_hash, 0xb29f6629)
    self.assertEquals(
        event_object.path, u'\\WINDOWS\\SYSTEM32\\PING.EXE')
    self.assertEquals(event_object.run_count, 14)
    self.assertEquals(event_object.volume_path, u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEquals(event_object.volume_serial, 0xac036525)

    expected_msg = (
        u'Superfetch [PING.EXE] was executed - run count 14 path: '
        u'\\WINDOWS\\SYSTEM32\\PING.EXE '
        u'hash: 0xB29F6629 '
        u'[ volume serial: 0xAC036525 '
        u'volume path: '
        u'\\DEVICE\\HARDDISKVOLUME1]')

    expected_msg_short = u'PING.EXE was run 14 time(s)'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testParse26(self):
    """Tests the Parse function on a version 26 Prefetch file."""
    test_file = os.path.join('test_data', 'TASKHOST.EXE-3AE259FC.pf')
    events = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(events)

    # Check the number of events in event container.
    self.assertEquals(len(event_container.events), 5)
    self.assertEquals(event_container.version, 26)

    # The last run time.
    event_object = event_container.events[0]

    # date -u -d"Oct 04, 2013 15:40:09.037833300 UTC" +"%s.%N"
    # 1380901209.037833300
    self.assertEquals(event_object.timestamp, 1380901209037833)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)
    self.assertEquals(event_object.executable, u'TASKHOST.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x3ae259fc)

    # The previous last run time.
    event_object = event_container.events[1]

    # date -u -d"Oct 04, 2013 15:28:09.010356500 UTC" +"%s.%N"
    # 1380900489.010356500
    self.assertEquals(event_object.timestamp, 1380900489010356)
    self.assertEquals(
        event_object.timestamp_desc,
        u'Previous {0:s}'.format(eventdata.EventTimestamp.LAST_RUNTIME))

    # The creation time.
    event_object = event_container.events[4]

    # date -u -d"Oct 04, 2013 15:57:26.146547600 UTC" +"%s.%N"
    # 1380902246.146547600
    self.assertEquals(event_object.timestamp, 1380902246146547)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)


if __name__ == '__main__':
  unittest.main()
