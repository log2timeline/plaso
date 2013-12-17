#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# pylint: disable-msg=W0611
from plaso.formatters import mcafeeav as mcafeeav_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import mcafeeav
from plaso.pvfs import utils

import pytz


class McafeeAccessProtectionUnitTest(unittest.TestCase):
  """A unit test for the McAfee AV Access Protection Log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'AccessProtectionLog.txt')
    self.input_file = utils.OpenOSFile(test_file)

    self.pre_obj = preprocess.PlasoPreprocess()
    self.pre_obj.zone = pytz.UTC

  def testParsing(self):
    """Test parsing of a McAfee AV Access Protection Log file."""
    parser = mcafeeav.McafeeAccessProtectionParser(self.pre_obj)

    self.input_file.seek(0)
    events = list(parser.Parse(self.input_file))

    # The file contains 14 lines.
    self.assertEquals(len(events), 14)

    # Test this entry:
    # 9/27/2013 2:42:26 PM  Blocked by Access Protection rule
    #   SOMEDOMAIN\someUser C:\Windows\System32\procexp64.exe C:\Program Files
    # (x86)\McAfee\Common Framework\UdaterUI.exe  Common Standard
    # Protection:Prevent termination of McAfee processes  Action blocked :
    # Terminate
    test_event1 = events[1]
    # And that the magic bytes get removed from the first line.
    test_event2 = events[0]

    self.assertEquals(test_event1.timestamp, 1380292959000000)
    self.assertEquals(test_event1.username, 'SOMEDOMAIN\\someUser')
    self.assertEquals(test_event1.full_path,
                      u'C:\\Windows\\System32\\procexp64.exe')

    self.assertEquals(test_event2.timestamp, 1380292946000000)

    expected_msg = (u'File Name: C:\\Windows\\System32\\procexp64.exe '
                    u'User: SOMEDOMAIN\\someUser '
                    u'C:\\Program Files (x86)\\McAfee\\Common Framework\\Frame'
                    u'workService.exe '
                    u'Blocked by Access Protection rule  '
                    u'Common Standard Protection:Prevent termination of McAfee '
                    u'processes '
                    u'Action blocked : Terminate')
    expected_short = (u'C:\\Windows\\System32\\procexp64.exe '
                      u'Action blocked : Terminate')

    msg, short = eventdata.EventFormatterManager.GetMessageStrings(test_event1)
    self.assertEquals(msg, expected_msg)
    self.assertEquals(short, expected_short)


if __name__ == '__main__':
  unittest.main()
