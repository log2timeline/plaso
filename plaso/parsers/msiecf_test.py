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
"""Tests for the Microsoft Internet Explorer (MSIE) Cache Files (CF) parser."""
import os
import unittest

from plaso.formatters import msiecf
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import msiecf


class MsiecfParserTest(unittest.TestCase):
  """Tests for the MSIE Cache Files (MSIECF) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = msiecf.MsiecfParser(pre_obj)

  def testMsiecfParserFile(self):
    """Reads and parses a test MSIE Cache File (MSIECF)."""
    test_file = os.path.join('test_data', 'index.dat')

    events = []
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # MSIE Cache File information:
    # 	File size:			32768 bytes
    # 	Number of items:		7
    # 	Number of recovered items:	11

    expected_number_of_events = 7 + 11
    self.assertEquals(len(events), expected_number_of_events)

    event_container = events[2]
    self.assertEquals(len(event_container), 4)

    # Record type             : URL
    # Offset range            : 21376 - 21632 (256)
    # Location                : Visited: testing@http://www.trafficfusionx.com
    #                           /download/tfscrn2/funnycats.exe
    # Primary time            : Jun 23, 2011 18:02:10.066000000
    # Secondary time          : Jun 23, 2011 18:02:10.066000000
    # Expiration time         : Jun 29, 2011 17:55:02
    # Last checked time       : Jun 23, 2011 18:02:12
    # Cache directory index   : -2 (0xfe)

    expected_location = (
        u'Visited: testing@http://www.trafficfusionx.com/download/tfscrn2'
        u'/funnycats.exe')

    self.assertEquals(event_container.offset, 21376)
    self.assertEquals(event_container.url, expected_location)
    self.assertEquals(event_container.cache_directory_index, -2)

    event_object = event_container.events[0]

    # date -u -d"Jun 23, 2011 18:02:10.066000000" +"%s.%N"
    self.assertEquals(event_object.timestamp,
                      (1308852130 * 1000000) + (66000000 / 1000))
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.LAST_VISITED_TIME)

    event_object = event_container.events[1]

    self.assertEquals(event_object.timestamp,
                      (1308852130 * 1000000) + (66000000 / 1000))
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.LAST_VISITED_TIME)

    # date -u -d"Jun 29, 2011 17:55:02" +"%s.%N"
    event_object = event_container.events[2]

    self.assertEquals(event_object.timestamp, 1309370102 * 1000000)
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.EXPIRATION_TIME)

    # date -u -d"Jun 23, 2011 18:02:12" +"%s.%N"
    event_object = event_container.events[3]

    self.assertEquals(event_object.timestamp, 1308852132 * 1000000)
    self.assertEquals(event_object.timestamp_desc, 'Last Checked Time')

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (u'Location: Visited: testing@http://www.trafficfusionx.com'
                    u'/download/tfscrn2/funnycats.exe '
                    u'Number of hits: 6 Cached file size: 0')

    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
