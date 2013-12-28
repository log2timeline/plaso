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
"""Tests for the Google Chrome history parser."""

import os
import unittest

from plaso.formatters import chrome
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers.sqlite_plugins import chrome
from plaso.parsers.sqlite_plugins import interface
from plaso.pvfs import utils

import pytz


class ChromeHistoryPluginTest(unittest.TestCase):
  """Tests for the Google Chrome history parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = chrome.ChromeHistoryPlugin(pre_obj)

  def testParseFile(self):
    """Read a Chrome History file and run a few tests."""
    test_file = os.path.join('test_data', 'History')

    events = None
    file_entry = utils.OpenOSFileEntry(test_file)
    with interface.SQLiteDatabase(file_entry) as database:
      generator = self.test_parser.Process(database)
      self.assertTrue(generator)
      events = list(generator)

    # The History file contains 71 events (69 page visits, 1 file downloads).
    self.assertEquals(len(events), 71)

    # Check the first page visited entry.
    event_object = events[0]

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.PAGE_VISITED)

    # date -u -d"2011-04-07 12:03:11.000000" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1302177791 * 1000000)

    expected_url = 'http://start.ubuntu.com/10.04/Google/'
    self.assertEquals(event_object.url, expected_url)

    expected_title = 'Ubuntu Start Page'
    self.assertEquals(event_object.title, expected_title)

    # Test the event specific formatter.
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
         u'%s (%s) [count: 0] Host: start.ubuntu.com '
         u'(URL not typed directly - no typed count)') % (
         expected_url, expected_title)

    self.assertEquals(msg, expected_msg)

    # Check the first file downloaded entry.
    event_object = events[69]

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.FILE_DOWNLOADED)

    # date -u -d"2011-05-23 08:35:30.000000" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1306139730 * 1000000)

    expected_url = ('http://fatloss4idiotsx.com/download/funcats/'
                    'funcats_scr.exe')
    self.assertEquals(event_object.url, expected_url)

    expected_full_path = '/home/john/Downloads/funcats_scr.exe'
    self.assertEquals(event_object.full_path, expected_full_path)

    # Test the event specific formatter.
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
         u'%s (%s). Received: 1132155 bytes out of: 1132155 bytes.') % (
         expected_url, expected_full_path)

    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
