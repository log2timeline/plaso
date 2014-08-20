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
"""Tests for the Android SMS plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import android_sms as android_sms_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import android_sms
from plaso.parsers.sqlite_plugins import test_lib


class AndroidSmsTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android SMS database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = android_sms.AndroidSmsPlugin()

  def testProcess(self):
    """Test the Process function on an Android SMS mmssms.db file."""
    test_file = self._GetTestFilePath(['mmssms.db'])
    event_generator = self._ParseDatabaseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # The SMS database file contains 9 events (5 SENT, 4 RECEIVED messages).
    self.assertEquals(len(event_objects), 9)

    # Check the first SMS sent.
    event_object = event_objects[0]

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-29 16:56:28.038000')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_address = u'1 555-521-5554'
    self.assertEquals(event_object.address, expected_address)

    expected_body = u'Yo Fred this is my new number.'
    self.assertEquals(event_object.body, expected_body)

    expected_msg = (
        u'Type: SENT '
        u'Address: 1 555-521-5554 '
        u'Status: READ '
        u'Message: Yo Fred this is my new number.')
    expected_short = u'Yo Fred this is my new number.'
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
