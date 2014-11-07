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
"""Tests for the Windows IIS log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import iis as iis_formatter
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import iis


__author__ = 'Ashley Holtz (ashley.a.holtz@gmail.com)'


class WinIISUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows IIS parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = iis.WinIISParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['iis.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 11)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-30 00:00:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.source_ip, u'10.10.10.100')
    self.assertEquals(event_object.dest_ip, u'10.10.10.100')
    self.assertEquals(event_object.dest_port, 80)

    expected_msg = (
        u'GET /some/image/path/something.jpg '
        u'[ 10.10.10.100 > 10.10.10.100 : 80 ] '
        u'Http Status: 200 '
        u'User Agent: Mozilla/4.0+(compatible;+Win32;'
        u'+WinHttp.WinHttpRequest.5)')
    expected_msg_short = (
        u'GET /some/image/path/something.jpg '
        u'[ 10.10.10.100 > 10.10.10.100 : 80 ]')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[5]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-30 00:00:05')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.http_method, 'GET')
    self.assertEquals(event_object.http_status, 200)
    self.assertEquals(
        event_object.requested_uri_stem, u'/some/image/path/something.jpg')

    event_object = event_objects[1]

    expected_msg = (
        u'GET /some/image/path/something.htm '
        u'[ 22.22.22.200 > 10.10.10.100 : 80 ] '
        u'Http Status: 404 '
        u'User Agent: Mozilla/5.0+(Macintosh;+Intel+Mac+OS+X+10_6_8)'
        u'+AppleWebKit/534.57.2+(KHTML,+like+Gecko)+Version/5.1.7'
        u'+Safari/534.57.2')
    expected_msg_short = (
        u'GET /some/image/path/something.htm '
        u'[ 22.22.22.200 > 10.10.10.100 : 80 ]')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

if __name__ == '__main__':
  unittest.main()
