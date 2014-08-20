#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""Parser test for utmp files."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import utmp as utmp_formatter
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import utmp


class UtmpParserTest(test_lib.ParserTestCase):
  """The unit test for UTMP parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = utmp.UtmpParser(pre_obj)

  def testParseUtmpFile(self):
    """Tests the Parse function for an UTMP file."""
    test_file = self._GetTestFilePath(['utmp'])
    events = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(events)
    self.assertEqual(len(event_objects), 14)
    event_object = event_objects[0]
    self.assertEqual(event_object.terminal, u'system boot')
    self.assertEqual(event_object.status, u'BOOT_TIME')
    event_object = event_objects[1]
    self.assertEqual(event_object.status, u'RUN_LVL')

    event_object = event_objects[2]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-13 14:45:09')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'LOGIN')
    self.assertEqual(event_object.computer_name, u'localhost')
    self.assertEqual(event_object.terminal, u'tty4')
    self.assertEqual(event_object.status, u'LOGIN_PROCESS')
    self.assertEqual(event_object.exit, 0)
    self.assertEqual(event_object.pid, 1115)
    self.assertEqual(event_object.terminal_id, 52)
    expected_msg = (
        u'User: LOGIN '
        u'Computer Name: localhost '
        u'Terminal: tty4 '
        u'PID: 1115 '
        u'Terminal_ID: 52 '
        u'Status: LOGIN_PROCESS '
        u'IP Address: localhost '
        u'Exit: 0')
    expected_msg_short = (
        u'User: LOGIN')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[12]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-18 22:46:56.305504')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.computer_name, u'localhost')
    self.assertEqual(event_object.terminal, u'pts/4')
    self.assertEqual(event_object.status, u'USER_PROCESS')
    self.assertEqual(event_object.exit, 0)
    self.assertEqual(event_object.pid, 2684)
    self.assertEqual(event_object.terminal_id, 13359)
    expected_msg = (
        u'User: moxilo '
        u'Computer Name: localhost '
        u'Terminal: pts/4 '
        u'PID: 2684 '
        u'Terminal_ID: 13359 '
        u'Status: USER_PROCESS '
        u'IP Address: localhost '
        u'Exit: 0')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testParseWtmpFile(self):
    """Tests the Parse function for an WTMP file."""
    test_file = self._GetTestFilePath(['wtmp.1'])
    events = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(events)
    self.assertEqual(len(event_objects), 4)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-12-01 17:36:38.432935')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'userA')
    self.assertEqual(event_object.computer_name, u'10.10.122.1')
    self.assertEqual(event_object.terminal, u'pts/32')
    self.assertEqual(event_object.status, u'USER_PROCESS')
    self.assertEqual(event_object.ip_address, u'10.10.122.1')
    self.assertEqual(event_object.exit, 0)
    self.assertEqual(event_object.pid, 20060)
    self.assertEqual(event_object.terminal_id, 842084211)
    expected_msg = (
        u'User: userA '
        u'Computer Name: 10.10.122.1 '
        u'Terminal: pts/32 '
        u'PID: 20060 '
        u'Terminal_ID: 842084211 '
        u'Status: USER_PROCESS '
        u'IP Address: 10.10.122.1 '
        u'Exit: 0')
    expected_msg_short = (
        u'User: userA')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
