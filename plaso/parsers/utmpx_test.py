#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Tests for UTMPX file parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import utmpx as utmpx_formatter
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import utmpx


class UtmpxParserTest(test_lib.ParserTestCase):
  """Tests for utmpx file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = utmpx.UtmpxParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['utmpx_mac'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 6)

    event_object = event_objects[0]
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-13 17:52:34')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg_short = u'User: N/A'
    expected_msg = (
        u'User: N/A Status: BOOT_TIME '
        u'Computer Name: localhost Terminal: N/A')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-13 17:52:41.736713')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.terminal, u'console', )
    self.assertEqual(event_object.status, u'USER_PROCESS')
    self.assertEqual(event_object.computer_name, u'localhost')
    expected_msg = (
        u'User: moxilo Status: '
        u'USER_PROCESS '
        u'Computer Name: localhost '
        u'Terminal: console')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[4]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-14 04:32:56.641464')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.terminal, u'ttys002')
    self.assertEqual(event_object.status, u'DEAD_PROCESS')
    expected_msg = (
        u'User: moxilo Status: '
        u'DEAD_PROCESS '
        u'Computer Name: localhost '
        u'Terminal: ttys002')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
