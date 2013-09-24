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
"""Parser Test for Windows Scheduled Task job files."""
import os
import unittest

# pylint: disable=W0611
from plaso.formatters import winjob as dummy_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import winjob

import pytz


class WinJobTest(unittest.TestCase):
  """The unit test for Windows Scheduled Task job parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self.test_parser = winjob.WinJobParser(pre_obj)


  def testParseFile(self):
    """Read a Windows Scheduled Task job file and make few tests."""
    test_file = os.path.join('test_data', 'wintask.job')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    self.assertEqual(len(events), 2)

    event_object = events[0]

    application_expected = (u'C:\\Program Files (x86)\\Google\\Update'
                            u'\\GoogleUpdate.exe')
    self.assertEqual(event_object.application, application_expected)

    username_expected = u'Brian'
    self.assertEqual(event_object.username, username_expected)

    description_expected = eventdata.EventTimestamp.LAST_RUNTIME
    self.assertEqual(event_object.timestamp_desc, description_expected)

    trigger_expected = u'DAILY'
    self.assertEqual(event_object.trigger, trigger_expected)

    comment_expected = (
        u'Keeps your Google software up to date. If this task is disabled or '
        u'stopped, your Google software will not be kept up to date, meaning '
        u'security vulnerabilities that may arise cannot be fixed and '
        u'features may not work. This task uninstalls itself when there is '
        u'no Google software using it.')
    self.assertEqual(event_object.comment, comment_expected)

    # 2013-08-24T12:42:00.112+00:00
    # expr `date -u -d"2013-08-24T12:42:00+00:00" +"%s"` \* 1000000 + 112000
    last_modified_date_expected = 1377348120112000
    self.assertEqual(event_object.timestamp,
        last_modified_date_expected)

    # Parse second event. Same metadata; different timestamp event.
    event_object = events[1]

    self.assertEqual(event_object.application, application_expected)
    self.assertEqual(event_object.username, username_expected)
    self.assertEqual(event_object.trigger, trigger_expected)
    self.assertEqual(event_object.comment, comment_expected)

    description_expected = 'Scheduled To Start'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    # 2013-07-12T15:42:00+00:00
    download_date_expected = 1373643720000000
    self.assertEqual(event_object.timestamp, download_date_expected)

    msg_expected = (
        u'Application: C:\\Program Files (x86)\\Google\\Update\\'
        u'GoogleUpdate.exe '
        u'/ua /installsource scheduler '
        u'Scheduled by: Brian '
        u'Run Iteration: DAILY')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event_object)

    self.assertEqual(msg_expected, msg)


if __name__ == '__main__':
  unittest.main()
