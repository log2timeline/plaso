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
"""Tests for the LS Quarantine database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import ls_quarantine as ls_quarantine_formatter
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import ls_quarantine
from plaso.parsers.sqlite_plugins import test_lib


class LSQuarantinePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the LS Quarantine database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = ls_quarantine.LsQuarantinePlugin()

  def testProcess(self):
    """Tests the Process function on a LS Quarantine database file."""
    test_file = self._GetTestFilePath(['quarantine.db'])
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The quarantine database contains 14 event_objects.
    self.assertEquals(len(event_objects), 14)

    # Examine a VLC event.
    event_object = event_objects[3]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-08 21:12:03')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.agent, u'Google Chrome')
    vlc_url = (
        u'http://download.cnet.com/VLC-Media-Player/3001-2139_4-10210434.html'
        u'?spi=40ab24d3c71594a5017d74be3b0c946c')
    self.assertEquals(event_object.url, vlc_url)

    self.assertTrue(u'vlc-2.0.7-intel64.dmg' in event_object.data)

    # Examine a MacKeeper event.
    event_object = event_objects[9]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-12 19:28:58')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    # Examine a SpeedTest event.
    event_object = event_objects[10]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-12 19:30:16')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    speedtest_message = (
        u'[Google Chrome] Downloaded: http://mackeeperapp.zeobit.com/aff/'
        u'speedtest.net.6/download.php?affid=460245286&trt=5&utm_campaign='
        u'3ES&tid_ext=P107fSKcSfqpMbcP3sI4fhKmeMchEB3dkAGpX4YIsvM;US;L;1 '
        u'<http://download.mackeeper.zeobit.com/package.php?'
        u'key=460245286&trt=5&landpr=Speedtest>')
    speedtest_short = (
        u'http://mackeeperapp.zeobit.com/aff/speedtest.net.6/download.php?'
        u'affid=4602452...')

    self._TestGetMessageStrings(
        event_object, speedtest_message, speedtest_short)


if __name__ == '__main__':
  unittest.main()
