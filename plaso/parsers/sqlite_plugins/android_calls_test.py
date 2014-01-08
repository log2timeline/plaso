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
"""Tests for the Android SMS call history plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import android_calls as android_calls_formatter
from plaso.lib import preprocess
from plaso.parsers.sqlite_plugins import test_lib
from plaso.parsers.sqlite_plugins import android_calls
from plaso.parsers.sqlite_plugins import interface
from plaso.pvfs import utils

import pytz


class AndroidCallSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android Call History database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self._plugin = android_calls.AndroidCallPlugin(pre_obj)

  def testProcess(self):
    """Test the Process function on an Android contacts2.db file."""
    test_file = self._GetTestFilePath(['contacts2.db'])
    event_generator = self._ParseDatabaseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # The contacts2 database file contains 5 events (MISSED/OUTGOING/INCOMING).
    self.assertEquals(len(event_objects), 5)

    # Check the first event.
    event_object = event_objects[0]

    self.assertEquals(event_object.timestamp_desc, u'Call Started')

    # date -u -d"2012-11-16T00:30:15.655000+00:00" +"%s.%N".
    self.assertEquals(event_object.timestamp, 1383772636690 * 1000)

    expected_number = u'5404561685'
    self.assertEquals(event_object.number, expected_number)

    expected_type = u'MISSED'
    self.assertEquals(event_object.call_type, expected_type)

    expected_call = (
        u'MISSED '
        u'Number: 5404561685 '
        u'Name: Barney '
        u'Duration: 0 seconds')
    expected_short = u'MISSED Call'
    self._TestGetMessageStrings(event_object, expected_call, expected_short)

    # Run some tests on the last 2 events.
    event_object_3 = event_objects[3]
    event_object_4 = event_objects[4]

    # Check the timestamp_desc of the last event.
    self.assertEquals(event_object_4.timestamp_desc, u'Call Ended')

    # Event 3: date -u -d"2013-11-07T00:03:36.690000+00:00" +"%s.%N".
    # Event 4: date -u -d"2013-11-07T00:14:15.690000+00:00" +"%s.%N".
    self.assertEquals(event_object_3.timestamp, 1383782616690 * 1000)
    self.assertEquals(event_object_4.timestamp, 1383783255690 * 1000)

    # Ensure the difference in btw. events 3 and 4 equals the duration.
    self.assertEquals(
            (event_object_4.timestamp - event_object_3.timestamp) / 1000000,
            event_object_4.duration)


if __name__ == '__main__':
  unittest.main()
