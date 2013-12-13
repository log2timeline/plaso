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
"""This file contains a unit test for the mactime parser in plaso."""
import os
import unittest

from plaso.formatters import mactime
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.lib import putils
from plaso.parsers import mactime

import pytz


class MactimeUnitTest(unittest.TestCase):
  """A unit test for the mactime parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'mactime.body')
    self.input_file = putils.OpenOSFile(test_file)

  def testParsing(self):
    """Test parsing of a mactime file."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    parser = mactime.MactimeParser(pre_obj, None)

    self.input_file.seek(0)
    events = list(parser.Parse(self.input_file))

    # The file contains 10 lines x 4 timestamps per line makes 40 events.
    self.assertEquals(len(events), 40)

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0
    test_event1 = events[8]
    test_event2 = events[9]
    test_event3 = events[10]
    test_event4 = events[11]

    self.assertEquals(test_event4.timestamp, 0)
    self.assertEquals(test_event4.timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)
    self.assertEquals(test_event4.inode, '16')

    self.assertEquals(test_event1.timestamp, 1337961583000000)
    self.assertEquals(test_event1.timestamp_desc,
                      eventdata.EventTimestamp.ACCESS_TIME)

    self.assertEquals(test_event2.timestamp, 1337961584000000)
    self.assertEquals(test_event2.timestamp_desc,
                      eventdata.EventTimestamp.MODIFICATION_TIME)

    self.assertEquals(test_event3.timestamp, 1337961585000000)
    self.assertEquals(test_event3.timestamp_desc,
                      eventdata.EventTimestamp.CHANGE_TIME)
    self.assertEquals(test_event3.name, '/a_directory/another_file')
    self.assertEquals(test_event3.mode_as_string, 'r/rrw-------')

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(test_event1)
    self.assertEquals(msg, u'/a_directory/another_file')


if __name__ == '__main__':
  unittest.main()
