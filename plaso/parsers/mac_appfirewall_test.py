#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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

import pytz
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import mac_appfirewall as mac_appfirewall_formatter
from plaso.lib import event
from plaso.parsers import mac_appfirewall
from plaso.parsers import test_lib


class MacAppFirewallUnitTest(test_lib.ParserTestCase):
  """Tests for Mac AppFirewall log file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.year = 2013
    pre_obj.zone = pytz.timezone('UTC')
    self._parser = mac_appfirewall.MacAppFirewallParser(pre_obj, None)

  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    test_file = self._GetTestFilePath(['appfirewall.log'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 47)

    event_object = event_objects[0]

    # date -u -d"Sat, 2 Nov 2013 04:07:35.222" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1383365255000000)
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

    # date -u -d"Sun, 3 Nov 2013 13:25:15.222" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1383485115000000)
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
    # date -u -d"Tue, 31 Dec 2013 23:59:23" +"%s"
    self.assertEqual(event_object.timestamp, 1388534363000000)

    event_object = event_objects[46]
    # date -u -d"Wed, 1 Jan 2014 01:13:23" +"%s"
    self.assertEqual(event_object.timestamp, 1388538803000000)


if __name__ == '__main__':
  unittest.main()
