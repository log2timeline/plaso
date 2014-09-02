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
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import msiecf as msiecf_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import msiecf
from plaso.parsers import test_lib


class MsiecfParserTest(test_lib.ParserTestCase):
  """Tests for the MSIE Cache Files (MSIECF) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = msiecf.MsiecfParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['index.dat'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # MSIE Cache File information:
    # 	File size:			32768 bytes
    # 	Number of items:		7
    # 	Number of recovered items:	11
    # 7 + 11 records, each with 4 records.

    self.assertEquals(len(event_objects), (7 + 11) * 4)

    # Record type             : URL
    # Offset range            : 21376 - 21632 (256)
    # Location                : Visited: testing@http://www.trafficfusionx.com
    #                           /download/tfscrn2/funnycats.exe
    # Primary time            : Jun 23, 2011 18:02:10.066000000
    # Secondary time          : Jun 23, 2011 18:02:10.066000000
    # Expiration time         : Jun 29, 2011 17:55:02
    # Last checked time       : Jun 23, 2011 18:02:12
    # Cache directory index   : -2 (0xfe)

    event_object = event_objects[8]
    expected_location = (
        u'Visited: testing@http://www.trafficfusionx.com/download/tfscrn2'
        u'/funnycats.exe')

    self.assertEquals(event_object.offset, 21376)
    self.assertEquals(event_object.url, expected_location)
    self.assertEquals(event_object.cache_directory_index, -2)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-06-23 18:02:10.066')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_VISITED_TIME)

    event_object = event_objects[9]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-06-23 18:02:10.066')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_VISITED_TIME)

    event_object = event_objects[10]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-06-29 17:55:02')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.EXPIRATION_TIME)

    event_object = event_objects[11]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-06-23 18:02:12')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_CHECKED_TIME)

    expected_msg = (
        u'Location: Visited: testing@http://www.trafficfusionx.com/download'
        u'/tfscrn2/funnycats.exe '
        u'Number of hits: 6 '
        u'Cached file size: 0')
    expected_msg_short = (
        u'Location: Visited: testing@http://www.trafficfusionx.com/download'
        u'/tfscrn2/fun...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
