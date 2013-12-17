#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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


"""Parser test for utmpx files."""
import os
import unittest

from plaso.parsers import utmpx
# pylint: disable=W0611
from plaso.formatters import utmpx as utmpx_formatter

from plaso.lib import preprocess
from plaso.lib import eventdata
from plaso.pvfs import utils

import pytz


class UtmpxParserTest(unittest.TestCase):
  """The unit test for UTMPX parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = utmpx.UtmpxParser(pre_obj, None)

  def testParseFile(self):
    """Read utmpx files and make few tests."""
    test_file = os.path.join('test_data', 'utmpx_mac')

    events = None
    with utils.OpenOSFile(test_file) as file_object:
      events = list(self.test_parser.Parse(file_object))

    self.assertEqual(len(events), 6)

    event = events[0]
    # date -u -d"Wed, 13 Nov 2013 17:52:34" +"%s.%N"
    self.assertEqual(1384365154000000, event.timestamp)
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_message = 'System boot time from utmpx.'
    self.assertEquals(msg, expected_message)

    event = events[1]
    self.assertEqual('moxilo', event.user)
    self.assertEqual('console', event. terminal)
    self.assertEqual('USER_PROCESS (0x07)', event.status)
    # date -u -d"Wed, 13 Nov 2013 17:52:41" +"%s736713"
    self.assertEqual(1384365161736713, event.timestamp)
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_message = (u'User: moxilo Status: '
                        u'USER_PROCESS (0x07) Terminal: console')
    expected_short_message = 'User: moxilo'
    self.assertEquals(msg, expected_message)
    self.assertEquals(msg_short, expected_short_message)

    event = events[3]
    self.assertEqual('N/A', event.user)
    self.assertEqual('N/A', event. terminal)
    self.assertEqual('EMPTY (0x00)', event.status)
    self.assertEqual(0, event.timestamp)
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_message = 'User: N/A Status: EMPTY (0x00) Terminal: N/A'
    expected_short_message = 'User: N/A'
    self.assertEquals(msg, expected_message)
    self.assertEquals(msg_short, expected_short_message)

    event = events[4]
    self.assertEqual('moxilo', event.user)
    self.assertEqual('ttys002', event. terminal)
    self.assertEqual('DEAD_PROCESS (0x08)', event.status)
    # date -u -d"Thu, 14 Nov 2013 04:32:56" +"%s641464"
    self.assertEqual(1384403576641464, event.timestamp)
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_message = (u'User: moxilo Status: '
                        u'DEAD_PROCESS (0x08) Terminal: ttys002')
    expected_short_message = 'User: moxilo'
    self.assertEquals(msg, expected_message)
    self.assertEquals(msg_short, expected_short_message)

if __name__ == '__main__':
  unittest.main()
