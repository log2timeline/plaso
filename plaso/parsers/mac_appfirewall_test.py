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
"""Tests for Mac AppFirewall log file parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import mac_appfirewall as mac_appfirewall_formatter
from plaso.lib import timelib_test
from plaso.parsers import mac_appfirewall
from plaso.parsers import test_lib


class MacAppFirewallUnitTest(test_lib.ParserTestCase):
  """Tests for Mac AppFirewall log file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = mac_appfirewall.MacAppFirewallParser()

  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    knowledge_base_values = {'year': 2013}
    test_file = self._GetTestFilePath(['appfirewall.log'])
    event_generator = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 47)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-02 04:07:35')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.agent, u'socketfilterfw[112]')
    self.assertEqual(event_object.computer_name, u'DarkTemplar-2.local')
    self.assertEqual(event_object.status, u'Error')
    self.assertEqual(event_object.process_name, u'Logging')
    self.assertEqual(event_object.action, u'creating /var/log/appfirewall.log')

    expected_msg = (
        u'Computer: DarkTemplar-2.local '
        u'Agent: socketfilterfw[112] '
        u'Status: Error '
        u'Process name: Logging '
        u'Log: creating /var/log/appfirewall.log')
    expected_msg_short = (
        u'Process name: Logging '
        u'Status: Error')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[9]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-03 13:25:15')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.agent, u'socketfilterfw[87]')
    self.assertEqual(event_object.computer_name, u'DarkTemplar-2.local')
    self.assertEqual(event_object.status, u'Info')
    self.assertEqual(event_object.process_name, u'Dropbox')
    self.assertEqual(event_object.action, u'Allow TCP LISTEN  (in:0 out:1)')

    expected_msg = (
        u'Computer: DarkTemplar-2.local '
        u'Agent: socketfilterfw[87] '
        u'Status: Info '
        u'Process name: Dropbox '
        u'Log: Allow TCP LISTEN  (in:0 out:1)')
    expected_msg_short = (
        u'Process name: Dropbox '
        u'Status: Info')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # Check repeated lines.
    event_object = event_objects[38]
    repeated_event_object = event_objects[39]
    self.assertEqual(event_object.agent, repeated_event_object.agent)
    self.assertEqual(
        event_object.computer_name, repeated_event_object.computer_name)
    self.assertEqual(event_object.status, repeated_event_object.status)
    self.assertEqual(
        event_object.process_name, repeated_event_object.process_name)
    self.assertEqual(event_object.action, repeated_event_object.action)

    # Year changes.
    event_object = event_objects[45]
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-31 23:59:23')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = event_objects[46]
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-01-01 01:13:23')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
