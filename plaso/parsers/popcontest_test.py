#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the Popularity Contest (popcontest) parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import popcontest as popcontest_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import popcontest
from plaso.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class PopularityContestUnitTest(test_lib.ParserTestCase):
  """Tests for the popcontest parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = popcontest.PopularityContestParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['popcontest1.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 13)

    self.assertEquals(
        event_objects[0].timestamp,
        timelib_test.CopyStringToTimestamp('2010-06-22 05:41:41.000'))
    expected_string = (
        u'Session 0 start '
        u'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_string = u'Session 0 start'
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[1].timestamp,
        timelib_test.CopyStringToTimestamp('2010-06-22 07:34:42.000'))
    expected_string = (u'mru [/usr/sbin/atd] package [at]')
    expected_short_string = u'/usr/sbin/atd'
    self._TestGetMessageStrings(
        event_objects[1], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[2].timestamp,
        timelib_test.CopyStringToTimestamp('2010-06-22 07:34:43.000'))
    expected_string = (
        u'mru [/usr/lib/python2.5/lib-dynload/_struct.so] '
        u'package [python2.5-minimal]')
    expected_short_string = u'/usr/lib/python2.5/lib-dynload/_struct.so'
    self._TestGetMessageStrings(
        event_objects[2], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[3].timestamp,
        timelib_test.CopyStringToTimestamp('2010-05-30 05:26:20.000'))
    expected_string = (
        u'mru [/usr/bin/empathy] package [empathy] tag [RECENT-CTIME]')
    expected_short_string = u'/usr/bin/empathy'
    self._TestGetMessageStrings(
        event_objects[3], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[6].timestamp,
        timelib_test.CopyStringToTimestamp('2010-05-12 07:58:33.000'))
    expected_string = (u'mru [/usr/bin/orca] package [gnome-orca] tag [OLD]')
    expected_short_string = u'/usr/bin/orca'
    self._TestGetMessageStrings(
        event_objects[6], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[7].timestamp,
        timelib_test.CopyStringToTimestamp('2010-06-22 05:41:41.000'))
    expected_string = u'Session 0 end'
    expected_short_string = expected_string
    self._TestGetMessageStrings(
        event_objects[7], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[8].timestamp,
        timelib_test.CopyStringToTimestamp('2010-06-22 05:41:41.000'))
    expected_string = (
        u'Session 1 start '
        u'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_string = u'Session 1 start'
    self._TestGetMessageStrings(
        event_objects[8], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[9].timestamp,
        timelib_test.CopyStringToTimestamp('2010-06-22 07:34:42.000'))
    expected_string = (u'mru [/super/cool/plasuz] package [plaso]')
    expected_short_string = u'/super/cool/plasuz'
    self._TestGetMessageStrings(
        event_objects[9], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[10].timestamp,
        timelib_test.CopyStringToTimestamp('2010-04-06 12:25:42.000'))
    expected_string = (u'mru [/super/cool/plasuz] package [miss_ctime]')
    expected_short_string = u'/super/cool/plasuz'
    self._TestGetMessageStrings(
        event_objects[10], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[11].timestamp,
        timelib_test.CopyStringToTimestamp('2010-05-12 07:58:33.000'))
    expected_string = (u'mru [/super/cool] package [plaso] tag [WRONG_TAG]')
    expected_short_string = u'/super/cool'
    self._TestGetMessageStrings(
        event_objects[11], expected_string, expected_short_string)

    self.assertEquals(
        event_objects[12].timestamp,
        timelib_test.CopyStringToTimestamp('2010-06-22 05:41:41.000'))
    expected_string = u'Session 1 end'
    expected_short_string = expected_string
    self._TestGetMessageStrings(
        event_objects[12], expected_string, expected_short_string)


if __name__ == '__main__':
  unittest.main()
