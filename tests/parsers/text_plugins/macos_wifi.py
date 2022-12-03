#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Wi-Fi log (wifi.log) files text parser plugin."""

import unittest

from plaso.parsers.text_plugins import macos_wifi

from tests.parsers.text_plugins import test_lib


class MacOSWiFiLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the MacOS MacOS Wi-Fi log (wifi.log) files text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = macos_wifi.MacOSWiFiLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['wifi.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'action': 'Interface en0 turn up.',
        'added_time': '0000-11-14T20:36:37.222+00:00',
        'agent': 'airportd[88]',
        'data_type': 'macos:wifi_log:entry',
        'function': 'airportdProcessDLILEvent',
        'text': 'en0 attached (up)'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Check year change.
    expected_event_values = {
        'action': 'Wi-Fi connected to SSID: AndroidAP',
        'added_time': '0001-01-01T01:12:17.311+00:00',
        'agent': 'airportd[88]',
        'data_type': 'macos:wifi_log:entry',
        'function': '_doAutoJoin',
        'text': 'Already associated to “AndroidAP”. Bailing on auto-join.'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 9)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithTurnedOverLog(self):
    """Tests the Process function with a turned over log file."""
    plugin = macos_wifi.MacOSWiFiLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['wifi_turned_over.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'action': None,
        'added_time': '0000-01-02T00:10:15+00:00',
        'agent': None,
        'data_type': 'macos:wifi_log:entry',
        'function': None,
        'text': 'test-macbookpro newsyslog[50498]: logfile turned over'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'action': None,
        'added_time': '0000-01-02T00:11:02.378+00:00',
        'agent': None,
        'data_type': 'macos:wifi_log:entry',
        'function': None,
        'text': (
            '<kernel> wl0: powerChange: *** '
            'BONJOUR/MDNS OFFLOADS ARE NOT RUNNING.')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
