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
"""Tests for utmpx file parser."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import utmpx as utmpx_formatter
from plaso.lib import event
from plaso.parsers import test_lib
from plaso.parsers import utmpx


class UtmpxParserTest(test_lib.ParserTestCase):
  """Tests for utmpx file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = utmpx.UtmpxParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['utmpx_mac'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 6)

    event_object = event_objects[0]

    # date -u -d"Wed, 13 Nov 2013 17:52:34" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1384365154000000)

    expected_string = (
        u'System boot time from utmpx.')
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[1]

    # date -u -d"Wed, 13 Nov 2013 17:52:41" +"%s736713"
    self.assertEqual(event_object.timestamp, 1384365161736713)
    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.terminal, u'console', )
    self.assertEqual(event_object.status, u'USER_PROCESS (0x07)')

    expected_msg = (
        u'User: moxilo Status: '
        u'USER_PROCESS (0x07) Terminal: console')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[3]

    self.assertEqual(event_object.timestamp, 0)
    self.assertEqual(event_object.user, u'N/A')
    self.assertEqual(event_object. terminal, u'N/A')
    self.assertEqual(event_object.status, u'EMPTY (0x00)')

    expected_msg = (
        u'User: N/A Status: EMPTY (0x00) Terminal: N/A')
    expected_msg_short = (
        u'User: N/A')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[4]

    # date -u -d"Thu, 14 Nov 2013 04:32:56" +"%s641464"
    self.assertEqual(event_object.timestamp, 1384403576641464)
    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.terminal, u'ttys002')
    self.assertEqual(event_object.status, u'DEAD_PROCESS (0x08)')

    expected_msg = (
        u'User: moxilo Status: '
        u'DEAD_PROCESS (0x08) Terminal: ttys002')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
