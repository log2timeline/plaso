#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Mac AppFirewall log file parser."""

import unittest

from plaso.parsers import mac_appfirewall

from tests.parsers import test_lib


class MacAppFirewallUnitTest(test_lib.ParserTestCase):
  """Tests for Mac AppFirewall log file parser."""

  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    parser = mac_appfirewall.MacAppFirewallParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['appfirewall.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 47)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action': 'creating /var/log/appfirewall.log',
        'agent': 'socketfilterfw[112]',
        'computer_name': 'DarkTemplar-2.local',
        'process_name': 'Logging',
        'status': 'Error',
        'timestamp': '2013-11-02 04:07:35.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Computer: DarkTemplar-2.local '
        'Agent: socketfilterfw[112] '
        'Status: Error '
        'Process name: Logging '
        'Log: creating /var/log/appfirewall.log')
    expected_short_message = (
        'Process name: Logging '
        'Status: Error')

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'action': 'Allow TCP LISTEN  (in:0 out:1)',
        'agent': 'socketfilterfw[87]',
        'computer_name': 'DarkTemplar-2.local',
        'process_name': 'Dropbox',
        'status': 'Info',
        'timestamp': '2013-11-03 13:25:15.000000'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    expected_message = (
        'Computer: DarkTemplar-2.local '
        'Agent: socketfilterfw[87] '
        'Status: Info '
        'Process name: Dropbox '
        'Log: Allow TCP LISTEN  (in:0 out:1)')
    expected_short_message = (
        'Process name: Dropbox '
        'Status: Info')

    event_data = self._GetEventDataOfEvent(storage_writer, events[9])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check repeated lines.
    event = events[38]
    event_data = self._GetEventDataOfEvent(storage_writer, event)

    repeated_event = events[39]
    repeated_event_data = self._GetEventDataOfEvent(
        storage_writer, repeated_event)

    self.assertEqual(event_data.agent, repeated_event_data.agent)
    self.assertEqual(
        event_data.computer_name, repeated_event_data.computer_name)
    self.assertEqual(event_data.status, repeated_event_data.status)
    self.assertEqual(
        event_data.process_name, repeated_event_data.process_name)
    self.assertEqual(event_data.action, repeated_event_data.action)

    # Year changes.
    expected_event_values = {
        'timestamp': '2013-12-31 23:59:23.000000'}

    self.CheckEventValues(storage_writer, events[45], expected_event_values)

    expected_event_values = {
        'timestamp': '2014-01-01 01:13:23.000000'}

    self.CheckEventValues(storage_writer, events[46], expected_event_values)


if __name__ == '__main__':
  unittest.main()
