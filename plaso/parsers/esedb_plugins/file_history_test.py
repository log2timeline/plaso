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
"""Tests for the File History ESE database file."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import file_history as file_history_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.esedb_plugins import file_history
from plaso.parsers.esedb_plugins import test_lib


class FileHistoryEseDbPluginTest(test_lib.EseDbPluginTestCase):
  """Tests for the File History ESE database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = file_history.FileHistoryEseDbPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_name = 'Catalog1.edb'
    event_queue_consumer = self._ParseEseDbFileWithPlugin(
        [test_file_name], self._plugin)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 2680)

    event_object = event_objects[693]

    self.assertEquals(event_object.usn_number, 9251162904)
    self.assertEquals(event_object.identifier, 356)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-12 17:34:36.688580')

    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    filename = u'?UP\\Favorites\\Links\\Lenovo'
    self.assertEquals(event_object.original_filename, filename)

    expected_msg = (
        u'Filename: {0:s} Identifier: 356 Parent Identifier: 230 Attributes: '
        u'16 USN number: 9251162904').format(filename)

    expected_msg_short = u'Filename: {0:s}'.format(filename)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
