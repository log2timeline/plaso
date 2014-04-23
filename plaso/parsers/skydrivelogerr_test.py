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
"""Tests for the SkyDriveLogErr log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import skydrivelogerr as skydrivelogerr_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers import skydrivelogerr as skydrivelogerr_parser
from plaso.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogErrorUnitTest(test_lib.ParserTestCase):
  """A unit test for the SkyDriveLogErr parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = skydrivelogerr_parser.SkyDriveLogErrorParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['skydriveerr.log'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 19)

    # expr `date -u -d "2013-07-25 16:03:23.291" +"%s%N"` \/ 1000
    self.assertEquals(event_objects[0].timestamp, 1374768203291000)
    # expr `date -u -d "13-07-25 16:03:24.649" +"%s%N"` \/ 1000
    self.assertEquals(event_objects[1].timestamp, 1374768204649000)
    # expr `date -u -d "13-08-01 21:27:44.124" +"%s%N"` \/ 1000
    self.assertEquals(event_objects[18].timestamp, 1375392464124000)

    expected_string = (u'Logging started. Version= 17.0.2011.0627 '
        '(StartLocalTime: 2013-07-25-180323.291 PID=0x8f4 TID=0x718 '
        'ContinuedFrom=)')
    expected_string_short = u'Logging started. Version= 17.0.2011.0627'
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string_short)

    expected_string = (u'[AUTH authapi.cpp(280)] Sign in failed : '
        'DRX_E_AUTH_NO_VALID_CREDENTIALS')
    expected_string_short = u'Sign in failed : DRX_E_AUTH_NO_VALID_CREDENTIALS'
    self._TestGetMessageStrings(
        event_objects[1], expected_string, expected_string_short)

    expected_string = (u'[WNS absconn.cpp(177)] Received data from server '
        '(dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  <ping-response>'
        '<wait>44</wait></ping-response>)')
    expected_string_short = u'Received data from server'
    self._TestGetMessageStrings(
        event_objects[18], expected_string, expected_string_short)


if __name__ == '__main__':
  unittest.main()
