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
"""Tests for the Zeitgeist parser."""
import os
import unittest

# pylint: disable-msg=W0611
from plaso.formatters import zeitgeist as zeitgeist_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import zeitgeist

import pytz


class ZeitgeistParserTest(unittest.TestCase):
  """Tests for the Zeitgeist parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = zeitgeist.ZeitgeistParser(pre_obj)

  def testParseFile(self):
    """Read a zeitgeist activity.sqlite file and run a few tests."""
    test_file = os.path.join('test_data', 'activity.sqlite')

    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # The sqlite file contains 44 events.
    self.assertEquals(len(events), 44)

    # Check the first event.
    event_object = events[0]

    expected_subject_uri = 'application://rhythmbox.desktop'
    self.assertEquals(event_object.subject_uri, expected_subject_uri)

    # expr `date -u -d"2013-10-22T08:53:19+00:00" +"%s"` \* 1000000 + 477000
    self.assertEquals(event_object.timestamp, 1382431999477000)

    # Test the event specific formatter.
    expected_msg = u'application://rhythmbox.desktop'
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event_object)
    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
