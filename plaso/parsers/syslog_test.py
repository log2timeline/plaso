#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""Tests for the syslog parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import syslog as syslog_formatter
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers import syslog
from plaso.parsers import test_lib


class SyslogUnitTest(test_lib.ParserTestCase):
  """Tests for the syslog parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.year = 2012
    self._parser = syslog.SyslogParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['syslog'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 13)

    # TODO let's add code to convert Jan 22 2012 07:52:33 into the
    # corresponding timestamp, I think that will be more readable
    self.assertEquals(event_objects[0].timestamp, 1327218753000000)
    self.assertEquals(event_objects[0].hostname, 'myhostname.myhost.com')

    expected_string = (
        u'[client, pid: 30840] : INFO No new content.')
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string)

    expected_msg = (
        '[aprocess, pid: 101001] : This is a multi-line message that screws up'
        'many syslog parsers.')
    expected_msg_short = (
        '[aprocess, pid: 101001] : This is a multi-line message that screws up'
        'many sys...')
    self._TestGetMessageStrings(
        event_objects[11], expected_msg, expected_msg_short)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-02-29 01:15:43')
    self.assertEquals(event_objects[6].timestamp, expected_timestamp)

    # Testing year increment.
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-03-23 23:01:18')
    self.assertEquals(event_objects[8].timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
