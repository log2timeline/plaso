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
"""This file contains the unit tests for the Symantec AV Log parser."""
import os
import unittest

# pylint: disable-msg=W0611
from plaso.formatters import symantec as symantec_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import symantec
from plaso.pvfs import utils

import pytz


class SymantecAccessProtectionUnitTest(unittest.TestCase):
  """A unit test for the Symantec AV Log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'Symantec.Log')
    self.input_file = utils.OpenOSFile(test_file)

    self.pre_obj = preprocess.PlasoPreprocess()
    self.pre_obj.zone = pytz.UTC

    self.maxDiff = None

  def testParsing(self):
    """Test parsing of a Symantec AV Log file."""
    parser = symantec.SymantecParser(self.pre_obj, None)

    self.input_file.seek(0)
    events = list(parser.Parse(self.input_file))

    # The file contains 8 lines.
    self.assertEquals(len(events), 8)

    # Test the second entry:
    test_event1 = events[1]

    self.assertEquals(test_event1.timestamp, 1354272449000000)
    self.assertEquals(test_event1.user, 'davnads')
    self.assertEquals(test_event1.file,
                      u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt')

    expected_msg = (u'Event Name: GL_EVENT_INFECTION; '
                    u'Category Name: GL_CAT_INFECTION; '
                    u'Malware Name: W32.Changeup!gen33; '
                    u'Malware Path: '
                    u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
                    u'Action0: Unknown; '
                    u'Action1: Clean virus from file; '
                    u'Action2: Delete infected file; '
                    u'Scan ID: 0; '
                    u'Event Data: 201\t4\t6\t1\t65542\t0\t0\t0\t0\t0\t0')
    expected_short = (u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
                      u'W32.Changeup!gen33; '
                      u'Unknown; ...')

    msg, short = eventdata.EventFormatterManager.GetMessageStrings(test_event1)
    self.assertEquals(msg, expected_msg)
    self.assertEquals(short, expected_short)


if __name__ == '__main__':
  unittest.main()
