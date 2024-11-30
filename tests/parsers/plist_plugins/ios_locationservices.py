#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple iOS routined application plist plugin."""

import unittest

from plaso.parsers.plist_plugins import ios_locationservices

from tests.parsers.plist_plugins import test_lib


class IOSRoutinedPlistPluginTest(test_lib.PlistPluginTestCase):
    """Tests for the Apple iOS routined application plist plugin."""

    def testProcess(self):
        """Tests the Process function."""
        plist_name = 'com.apple.routined.plist'

        plugin = ios_locationservices.RoutinedPlistPlugin()
        storage_writer = self._ParsePlistFileWithPlugin(
            plugin, [plist_name], plist_name)

        # Check the number of event data entries extracted.
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            'event_data')
        self.assertGreater(number_of_event_data, 0)  # Ensure some events were parsed.

        # Check for warnings during extraction.
        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            'extraction_warning')
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            'recovery_warning')
        self.assertEqual(number_of_recovery_warnings, 0)

        # Verify one of the extracted events.
        expected_event_values = {
            'key': 'LastAssetUpdateDate',
            'data_type': 'ios:routined:entry',
            'value': '2023-05-20T01:42:40+00:00'  # Example expected timestamp.
        }

        event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
    unittest.main()
