#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the Microsoft Internet Explorer WebCache database."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import msie_webcache as msie_webcache_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.esedb_plugins import msie_webcache
from plaso.parsers.esedb_plugins import test_lib


class MsieWebCacheEseDbPluginTest(test_lib.EseDbPluginTestCase):
  """Tests for the MSIE WebCache ESE database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = msie_webcache.MsieWebCacheEseDbPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_name = 'WebCacheV01.dat'
    event_queue_consumer = self._ParseEseDbFileWithPlugin(
        [test_file_name], self._plugin)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 1354)

    event_object = event_objects[0]

    self.assertEquals(event_object.container_identifier, 1)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-05-12 07:30:25.486198')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)

    expected_msg = (
        u'Container identifier: 1 '
        u'Set identifier: 0 '
        u'Name: Content '
        u'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        u'INetCache\\IE\\ '
        u'Table: Container_1')
    expected_msg_short = (
        u'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        u'INetCache\\IE\\')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
