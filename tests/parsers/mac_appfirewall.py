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
        'data_type': 'mac:appfirewall:line',
        'process_name': 'Logging',
        'status': 'Error',
        'timestamp': '2013-11-02 04:07:35.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'action': 'Allow TCP LISTEN  (in:0 out:1)',
        'agent': 'socketfilterfw[87]',
        'computer_name': 'DarkTemplar-2.local',
        'data_type': 'mac:appfirewall:line',
        'process_name': 'Dropbox',
        'status': 'Info',
        'timestamp': '2013-11-03 13:25:15.000000'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    # Check repeated lines.
    event_data = self._GetEventDataOfEvent(storage_writer, events[38])

    expected_event_values = {
        'action': event_data.action,
        'agent': event_data.agent,
        'computer_name': event_data.computer_name,
        'data_type': 'mac:appfirewall:line',
        'process_name': event_data.process_name,
        'status': event_data.status}

    self.CheckEventValues(storage_writer, events[39], expected_event_values)

    # Year changes.
    expected_event_values = {
        'data_type': 'mac:appfirewall:line',
        'timestamp': '2013-12-31 23:59:23.000000'}

    self.CheckEventValues(storage_writer, events[45], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:appfirewall:line',
        'timestamp': '2014-01-01 01:13:23.000000'}

    self.CheckEventValues(storage_writer, events[46], expected_event_values)


if __name__ == '__main__':
  unittest.main()
