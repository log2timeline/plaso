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
"""Tests for the Skype main.db history parser."""
import os
import unittest

# pylint: disable-msg=W0611
from plaso.formatters import skype as dummy_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import skype

import pytz


class SkypParserTest(unittest.TestCase):
  """Tests for the Skye main.db history parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = skype.SkypeParser(pre_obj)

  def testParseFile(self):
    """Read a skype history file and run a few tests."""
    test_file = os.path.join('test_data', 'skype_main.db')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # The History file contains 14 events.
    self.assertEquals(len(events), 14)

    sources = {}
    for event_object in events:
      description = event_object.timestamp_desc
      if description in sources:
        sources[description] += 1
      else:
        sources[description] = 1

    written_time = eventdata.EventTimestamp.WRITTEN_TIME
    self.assertEquals(len(sources.keys()), 2)
    self.assertEquals(sources['Profile Changed'], 1)
    self.assertEquals(sources[written_time], 13)

    # Check the first page visited entry.
    event_object = events[0]

    # date -u -d"2013-07-30T21:22:08+00:00"
    self.assertEquals(event_object.timestamp, 1375219588000000)

    # Test the event specific formatter.
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
        'From: Gen Beringer <gen.beringer> To: european.bbq.competitor '
        'Message: yt? [european.bbq.competitor | yt?]')

    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
