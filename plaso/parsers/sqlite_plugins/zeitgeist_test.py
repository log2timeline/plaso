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
"""Tests for the Zeitgeist activity database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import zeitgeist as zeitgeist_formatter
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import test_lib
from plaso.parsers.sqlite_plugins import zeitgeist


class ZeitgeistPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Zeitgeist activity database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._plugin = zeitgeist.ZeitgeistPlugin(pre_obj)

  def testProcess(self):
    """Tests the Process function on a Zeitgeist activity database file."""
    test_file = self._GetTestFilePath(['activity.sqlite'])
    event_generator = self._ParseDatabaseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # The sqlite file contains 44 events.
    self.assertEquals(len(event_objects), 44)

    # Check the first event.
    event_object = event_objects[0]

    expected_subject_uri = u'application://rhythmbox.desktop'
    self.assertEquals(event_object.subject_uri, expected_subject_uri)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-22 08:53:19.477')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = u'application://rhythmbox.desktop'
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
