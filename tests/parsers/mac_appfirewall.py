#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Mac AppFirewall log file parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import mac_appfirewall as mac_appfirewall_formatter
from plaso.lib import timelib
from plaso.parsers import mac_appfirewall

from tests.parsers import test_lib


class MacAppFirewallUnitTest(test_lib.ParserTestCase):
  """Tests for Mac AppFirewall log file parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = mac_appfirewall.MacAppFirewallParser()

  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    knowledge_base_values = {u'year': 2013}
    test_file = self._GetTestFilePath([u'appfirewall.log'])
    event_queue_consumer = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 47)

    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-02 04:07:35')
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

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-03 13:25:15')
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
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-31 23:59:23')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = event_objects[46]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-01 01:13:23')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
