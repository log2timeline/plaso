#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple iOS WiFi Known Networks plist plugin."""

import unittest

from plaso.parsers.plist_plugins import ios_wifi_known_networks

from tests.parsers.plist_plugins import test_lib


class IOSWiFiKnownNetworksPlistPluginTest(test_lib.PlistPluginTestCase):
    """Tests for the Apple iOS WiFi Known Networks plist plugin."""

    def testProcess(self):
        """Tests the Process function."""
        plist_name = 'com.apple.wifi.known-networks.plist'

        plugin = ios_wifi_known_networks.IOSWiFiKnownNetworksPlistPlugin()
        storage_writer = self._ParsePlistFileWithPlugin(
            plugin, [plist_name], plist_name)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            'event_data')
        self.assertEqual(number_of_event_data, 9)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            'extraction_warning')
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            'recovery_warning')
        self.assertEqual(number_of_recovery_warnings, 0)

        expected_event_values = {
            'ssid': 'wifi.network.ssid.Matt_Foley',
            'bssid': '76:a7:41:e7:7c:9d',
            'data_type': 'ios:wifi:known_networks:knowing',
            'channel': 1,
            'added_at': '2023-04-15T13:53:47+00:00',
            'last_associated': '2023-05-14T01:15:45+00:00'}

        event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
    unittest.main()
