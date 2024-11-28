# -*- coding: utf-8 -*-
"""Tests for the SQLite parser plugin for iOS accounts database files."""

import unittest

from plaso.parsers.sqlite_plugins import android_app_launch

from tests.parsers.sqlite_plugins import test_lib


class AndroidAppLaunchPluginTest(test_lib.SQLitePluginTestCase):
    """Tests for the SQLite parser plugin for Android App Launch database files."""

    def testParse(self):
        """Tests the ParseAccountRow method."""
        plugin = android_app_launch.AndroidAppLaunchPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ['SimpleStorage'], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            'event_data')
        self.assertEqual(number_of_event_data, 411)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            'extraction_warning')
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            'date': '2022-12-04T19:03:23.097+00:00', 
            'package_name': 'ws.coverme.im',
            'launch_location_id': '1000'
        }

        event_data = storage_writer.GetAttributeContainerByIndex('event_data', 69)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
    unittest.main() 