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
"""Tests for the selinux log file parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import selinux as selinux_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers import selinux
from plaso.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SELinuxUnitTest(test_lib.ParserTestCase):
  """Tests for the selinux log file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.year = 2013
    self._parser = selinux.SELinuxParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['selinux.log'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 5)

    # Test case: normal entry.
    event_object = event_objects[0]

    self.assertEquals(event_object.timestamp, 1337845201174000)

    expected_msg = (
        u'[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        u'auid=4294967295 new auid=0 old ses=4294967295 new ses=1165')
    expected_msg_short = (
        u'[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        u'auid=4294967295 new auid=...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # Test case: short date.
    event_object = event_objects[1]

    self.assertEquals(event_object.timestamp, 1337845201000000)

    expected_string = u'[audit_type: SHORTDATE] check rounding'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Test case: no msg.
    event_object = event_objects[2]

    self.assertEquals(event_object.timestamp, 1337845222174000)

    expected_string = u'[audit_type: NOMSG]'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Test case: under score.
    event_object = event_objects[3]

    self.assertEquals(event_object.timestamp, 1337845666174000)

    expected_msg = (
        u'[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        u'auid=4294967295 new auid=54321 old ses=4294967295 new ses=1166')
    expected_msg_short = (
        u'[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        u'auid=4294967295 new...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
