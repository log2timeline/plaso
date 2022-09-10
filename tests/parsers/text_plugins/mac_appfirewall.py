#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac AppFirewall log file text parser plugin."""

import unittest

from plaso.parsers.text_plugins import mac_appfirewall

from tests.parsers.text_plugins import test_lib


class MacAppFirewallTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Mac AppFirewall log file text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = mac_appfirewall.MacAppFirewallTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['appfirewall.log'], plugin, knowledge_base_values={'year': 2013})

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 47)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action': 'creating /var/log/appfirewall.log',
        'agent': 'socketfilterfw[112]',
        'computer_name': 'DarkTemplar-2.local',
        'data_type': 'mac:appfirewall:line',
        'date_time': '2013-11-02 04:07:35',
        'process_name': 'Logging',
        'status': 'Error'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'action': 'Allow TCP LISTEN  (in:0 out:1)',
        'agent': 'socketfilterfw[87]',
        'computer_name': 'DarkTemplar-2.local',
        'data_type': 'mac:appfirewall:line',
        'date_time': '2013-11-03 13:25:15',
        'process_name': 'Dropbox',
        'status': 'Info'}

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
        'date_time': '2013-12-31 23:59:23'}

    self.CheckEventValues(storage_writer, events[45], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:appfirewall:line',
        'date_time': '2014-01-01 01:13:23'}

    self.CheckEventValues(storage_writer, events[46], expected_event_values)


if __name__ == '__main__':
  unittest.main()
