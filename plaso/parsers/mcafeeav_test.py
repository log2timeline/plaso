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
"""This file contains the unit tests for the McAfee AV Log parsers in plaso."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import mcafeeav as mcafeeav_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import mcafeeav
from plaso.parsers import test_lib

import pytz


class McafeeAccessProtectionUnitTest(test_lib.ParserTestCase):
  """A unit test for the McAfee AV Access Protection Log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self._parser = mcafeeav.McafeeAccessProtectionParser(pre_obj)

  def testParse(self):
    """Tests the Parse function."""
    test_file = os.path.join('test_data', 'AccessProtectionLog.txt')
    events = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(events)

    # The file contains 14 lines which results in 14 event objects.
    self.assertEquals(len(event_objects), 14)

    # Test that the UTF-8 byte order mark gets removed from the first line.
    event_object = event_objects[0]

    self.assertEquals(event_object.timestamp, 1380292946000000)

    # Test this entry:
    # 9/27/2013 2:42:26 PM  Blocked by Access Protection rule
    #   SOMEDOMAIN\someUser C:\Windows\System32\procexp64.exe C:\Program Files
    # (x86)\McAfee\Common Framework\UdaterUI.exe  Common Standard
    # Protection:Prevent termination of McAfee processes  Action blocked :
    # Terminate

    event_object = event_objects[1]

    self.assertEquals(event_object.timestamp, 1380292959000000)
    self.assertEquals(event_object.username, u'SOMEDOMAIN\\someUser')
    self.assertEquals(
        event_object.full_path, u'C:\\Windows\\System32\\procexp64.exe')

    expected_msg = (
        u'File Name: C:\\Windows\\System32\\procexp64.exe '
        u'User: SOMEDOMAIN\\someUser '
        u'C:\\Program Files (x86)\\McAfee\\Common Framework\\Frame'
        u'workService.exe '
        u'Blocked by Access Protection rule  '
        u'Common Standard Protection:Prevent termination of McAfee processes '
        u'Action blocked : Terminate')
    expected_msg_short = (
        u'C:\\Windows\\System32\\procexp64.exe '
        u'Action blocked : Terminate')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
