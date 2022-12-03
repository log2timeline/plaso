#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Application firewall log file text parser plugin."""

import unittest

from plaso.parsers.text_plugins import macos_appfirewall

from tests.parsers.text_plugins import test_lib


class MacOSAppFirewallTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the MacOS Application firewall log file text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = macos_appfirewall.MacOSAppFirewallTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['appfirewall.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 47)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Note that added_time contains a date time delta.
    expected_event_values = {
        'action': 'Allow TCP LISTEN  (in:0 out:1)',
        'added_time': '0000-11-29T22:17:30+00:00',
        'agent': 'socketfilterfw[87]',
        'computer_name': 'DarkTemplar-2.local',
        'data_type': 'macos:appfirewall_log:entry',
        'process_name': 'Spotify',
        'status': 'Info'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 38)
    self.CheckEventData(event_data, expected_event_values)

    # Check repeated lines.
    expected_event_values['added_time'] = '0000-11-29T22:18:29+00:00'

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 39)
    self.CheckEventData(event_data, expected_event_values)

    # Check year change.
    expected_event_values = {
        'action': 'Allow TCP LISTEN  (in:0 out:1)',
        'added_time': '0001-01-01T01:13:23+00:00',
        'agent': 'socketfilterfw[87]',
        'computer_name': 'DarkTemplar-2.local',
        'data_type': 'macos:appfirewall_log:entry',
        'process_name': 'Notify',
        'status': 'Info'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 46)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
