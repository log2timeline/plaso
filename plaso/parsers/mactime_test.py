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
"""This file contains a unit test for the mactime parser in plaso."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import mactime as mactime_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import mactime
from plaso.parsers import test_lib

import pytz


class MactimeUnitTest(test_lib.ParserTestCase):
  """A unit test for the mactime parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self._parser = mactime.MactimeParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = os.path.join('test_data', 'mactime.body')
    events = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(events)

    # The file contains 10 lines x 4 timestamps per line this will result in
    # 40 event objects.
    self.assertEquals(len(event_objects), 40)

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0
    event_object = event_objects[11]

    self.assertEquals(event_object.timestamp, 0)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEquals(event_object.inode, u'16')

    event_object = event_objects[8]

    self.assertEquals(event_object.timestamp, 1337961583000000)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)

    expected_string = u'/a_directory/another_file'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[9]

    self.assertEquals(event_object.timestamp, 1337961584000000)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    event_object = event_objects[10]

    self.assertEquals(event_object.timestamp, 1337961585000000)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CHANGE_TIME)
    self.assertEquals(event_object.name, u'/a_directory/another_file')
    self.assertEquals(event_object.mode_as_string, u'r/rrw-------')


if __name__ == '__main__':
  unittest.main()
