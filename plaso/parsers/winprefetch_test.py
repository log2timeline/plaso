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

import unittest

# pylint: disable=unused-import
from plaso.formatters import winprefetch as winprefetch_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers import test_lib
from plaso.parsers import winprefetch


class WinPrefetchParserTest(test_lib.ParserTestCase):
  """Tests for the Windows prefetch parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = winprefetch.WinPrefetchParser(pre_obj)

  def testParse17(self):
    """Tests the Parse function on a version 17 Prefetch file."""
    test_file = self._GetTestFilePath(['CMD.EXE-087B4001.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(event_generator)

    self.assertEquals(len(event_container.events), 2)
    self.assertEquals(event_container.version, 17)

    # The last run time.
    event_object = event_container.events[1]

    # date -u -d"Mar 10, 2013 10:11:49.281250000 UTC" +"%s.%N"
    # 1362910309.281250000
    self.assertEquals(event_object.timestamp, 1362910309281250)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)
    self.assertEquals(event_object.executable, u'CMD.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x087b4001)

    # The creation time.
    event_object = event_container.events[0]

    # date -u -d "Mar 10, 2013 10:19:46.234375000 UTC" +"%s.%N"
    # 1362910786.234375000
    self.assertEquals(event_object.timestamp, 1362910786234375)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

  def testParse23(self):
    """Tests the Parse function on a version 23 Prefetch file."""
    test_file = self._GetTestFilePath(['PING.EXE-B29F6629.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(event_generator)

    self.assertEquals(len(event_container.events), 2)
    self.assertEquals(event_container.version, 23)

    # The last run time.
    event_object = event_container.events[1]

    # Date: 2012-04-06T19:00:55.932955+00:00.
    self.assertEquals(event_object.timestamp, 1333738855932955)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)

    # The creation time.
    event_object = event_container.events[0]

    # Date: 2010-11-10T17:37:26.484375+00:00.
    self.assertEquals(event_object.timestamp, 1289410646484375)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    self.assertEquals(event_object.executable, u'PING.EXE')
    self.assertEquals(event_object.prefetch_hash, 0xb29f6629)
    self.assertEquals(
        event_object.path, u'\\WINDOWS\\SYSTEM32\\PING.EXE')
    self.assertEquals(event_object.run_count, 14)
    self.assertEquals(
        event_object.volume_device_paths[0], u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEquals(event_object.volume_serial_numbers[0], 0xac036525)

    expected_msg = (
        u'Prefetch [PING.EXE] was executed - run count 14 path: '
        u'\\WINDOWS\\SYSTEM32\\PING.EXE '
        u'hash: 0xB29F6629 '
        u'volume: 1 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUME1]')

    expected_msg_short = u'PING.EXE was run 14 time(s)'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testParse23MultiVolume(self):
    """Tests the Parse function on a mulit volume version 23 Prefetch file."""
    test_file = self._GetTestFilePath(['WUAUCLT.EXE-830BCC14.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(event_generator)

    self.assertEquals(len(event_container.events), 6)
    self.assertEquals(event_container.version, 23)

    # The last run time.
    event_object = event_container.events[5]

    # TODO: update after date time test function code clean up.
    # Thu Mar 15 21:17:39.807996 UTC 2012
    self.assertEquals(event_object.timestamp, 1331846259807996)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)

    # The creation time.
    event_object = event_container.events[0]

    # TODO: update after date time test function code clean up.
    # Wed Nov 10 17:37:26.484375 UTC 2010
    self.assertEquals(event_object.timestamp, 1289410646484375)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    self.assertEquals(event_object.executable, u'WUAUCLT.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x830bcc14)
    self.assertEquals(
        event_object.path, u'\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE')
    self.assertEquals(event_object.run_count, 25)
    self.assertEquals(
        event_object.volume_device_paths[0], u'\\DEVICE\\HARDDISKVOLUME1')
    self.assertEquals(event_object.volume_serial_numbers[0], 0xac036525)

    expected_msg = (
        u'Prefetch [WUAUCLT.EXE] was executed - run count 25 path: '
        u'\\WINDOWS\\SYSTEM32\\WUAUCLT.EXE '
        u'hash: 0x830BCC14 '
        u'volume: 1 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUME1], '
        u'volume: 2 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY2], '
        u'volume: 3 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY4], '
        u'volume: 4 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY7], '
        u'volume: 5 [serial number: 0xAC036525, '
        u'device path: \\DEVICE\\HARDDISKVOLUMESHADOWCOPY8]')

    expected_msg_short = u'WUAUCLT.EXE was run 25 time(s)'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testParse26(self):
    """Tests the Parse function on a version 26 Prefetch file."""
    test_file = self._GetTestFilePath(['TASKHOST.EXE-3AE259FC.pf'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(event_generator)

    self.assertEquals(len(event_container.events), 5)
    self.assertEquals(event_container.version, 26)

    # The last run time.
    event_object = event_container.events[1]

    # date -u -d"Oct 04, 2013 15:40:09.037833300 UTC" +"%s.%N"
    # 1380901209.037833300
    self.assertEquals(event_object.timestamp, 1380901209037833)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)
    self.assertEquals(event_object.executable, u'TASKHOST.EXE')
    self.assertEquals(event_object.prefetch_hash, 0x3ae259fc)

    # The previous last run time.
    event_object = event_container.events[2]

    # date -u -d"Oct 04, 2013 15:28:09.010356500 UTC" +"%s.%N"
    # 1380900489.010356500
    self.assertEquals(event_object.timestamp, 1380900489010356)
    self.assertEquals(
        event_object.timestamp_desc,
        u'Previous {0:s}'.format(eventdata.EventTimestamp.LAST_RUNTIME))

    # The creation time.
    event_object = event_container.events[0]

    # date -u -d"Oct 04, 2013 15:57:26.146547600 UTC" +"%s.%N"
    # 1380902246.146547600
    self.assertEquals(event_object.timestamp, 1380902246146547)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)


if __name__ == '__main__':
  unittest.main()
