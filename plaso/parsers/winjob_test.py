#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Tests for the Windows Scheduled Task job file parser."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winjob as winjob_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import test_lib
from plaso.parsers import winjob

import pytz


class WinJobTest(test_lib.ParserTestCase):
  """Tests for the Windows Scheduled Task job file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self._parser = winjob.WinJobParser(pre_obj)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['wintask.job'])
    events = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(events)

    self.assertEquals(len(event_container.events), 2)

    event_object = event_container.events[0]

    application_expected = (
        u'C:\\Program Files (x86)\\Google\\Update\\GoogleUpdate.exe')
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
    event_object = event_container.events[1]

    self.assertEqual(event_object.application, application_expected)
    self.assertEqual(event_object.username, username_expected)
    self.assertEqual(event_object.trigger, trigger_expected)
    self.assertEqual(event_object.comment, comment_expected)

    description_expected = u'Scheduled To Start'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    # 2013-07-12T15:42:00+00:00
    download_date_expected = 1373643720000000
    self.assertEqual(event_object.timestamp, download_date_expected)

    expected_msg = (
        u'Application: C:\\Program Files (x86)\\Google\\Update\\'
        u'GoogleUpdate.exe /ua /installsource scheduler '
        u'Scheduled by: Brian '
        u'Run Iteration: DAILY')

    expected_msg_short = (
        u'Application: C:\\Program Files (x86)\\Google\\Update\\'
        u'GoogleUpdate.exe /ua /insta...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
