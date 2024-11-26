# -*- coding: utf-8 -*-
"""Tests for the SQLite parser plugin for iOS accounts database files."""

import unittest

from plaso.parsers.sqlite_plugins import ios_accounts

from tests.parsers.sqlite_plugins import test_lib


class IOSAccountsPluginTest(test_lib.SQLitePluginTestCase):
    """Tests for the SQLite parser plugin for iOS accounts database files."""

    def testParse(self):
        """Tests the ParseAccountRow method."""
        plugin = ios_accounts.IOSAccountsPlugin()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ['Accounts3.sqlite'], plugin)
        
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            'event_data')
        self.assertEqual(number_of_event_data, 18)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            'extraction_warning')
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            'date': '2020-08-27T11:13:11.912371+00:00', 
            'account_type': 'iCloud',
            'identifier': '1589F4EC-8F6C-4F37-929F-C6F121B36A59',
            'owning_bundle_id': 'com.apple.purplebuddy',
            'username': 'thisisdfir@gmail.com'
        }

        event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
    unittest.main()