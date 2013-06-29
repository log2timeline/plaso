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
"""Tests for the Windows recycler parser."""
import os
import unittest

from plaso.formatters import recycler
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import recycler


class WinRecyclerParserTest(unittest.TestCase):
  """Tests for the Windows recycler parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.info2_parser = recycler.WinInfo2Parser(pre_obj)
    self.i_parser = recycler.WinRecycleParser(pre_obj)

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testParseIFile(self):
    """Read an $Ixxx file and run a few tests."""
    test_file = os.path.join('test_data', '$II3DF3L.zip')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.i_parser.Parse(file_object))

    self.assertEquals(len(events), 1)

    event_object = events[0]

    self.assertEquals(event_object.orig_filename, (
        u'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip'))

    self.assertEquals(event_object.timestamp, 1331585398633000)
    self.assertEquals(event_object.file_size, 724919)

    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
        event_object)
    expected_short_string = (
        u'Deleted file: C:\\Users\\nfury\\Documents\\Alloy Research\\'
        'StarFury.zip')
    expected_string = (
        u'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip '
        '(from drive C?)')
    self.assertEquals(msg, expected_string)
    self.assertEquals(msg_short, expected_short_string)

  def testParseInfo2(self):
    """Read an INFO2 file and run a few tests."""
    test_file = os.path.join('test_data', 'INFO2')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.info2_parser.Parse(file_object))

    self.assertEquals(len(events), 4)

    # Date: 2004-08-25T16:18:25.237000+00:00
    self.assertEquals(events[0].timestamp, 1093450705237000)
    self.assertEquals(events[0].timestamp_desc,
                      eventdata.EventTimestamp.DELETED_TIME)

    self.assertEquals(events[0].index, 1)
    self.assertEquals(events[0].orig_filename, (
        u'C:\\Documents and Settings\\Mr. Evil\\Desktop\\lalsetup250.exe'))


    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(events[1])
    self.assertEquals(msg, (
        u'DC2 -> C:\\Documents and Settings\\Mr. '
        'Evil\\Desktop\\netstumblerinstaller_0_4_0.exe [C:\\Documents and '
        'Settings\\Mr. Evil\\Desktop\\netstumblerinstaller_0_4_0.exe] (from '
        'drive C)'))

    short, source = eventdata.EventFormatterManager.GetSourceStrings(
        events[2])

    self.assertEquals(source, 'Recycle Bin')
    self.assertEquals(short, 'RECBIN')


if __name__ == '__main__':
  unittest.main()
