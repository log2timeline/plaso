# -*- coding: utf-8 -*-
"""Tests for the MyRoutinedPlistPlugin."""

import unittest

from plaso.parsers.plist_plugins import ios_locationservices
from tests.parsers.plist_plugins import test_lib


class MyRoutinedPlistPluginTest(test_lib.PlistPluginTestCase):
    """Tests for the MyRoutinedPlistPlugin."""

    def testProcess(self):
        plist_name = 'com.apple.routined.plist'
        plugin = ios_locationservices.MyRoutinedPlistPlugin()
        storage_writer = self._ParsePlistFileWithPlugin(
            plugin, [plist_name], plist_name)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            'event_data')
        self.assertEqual(number_of_event_data, 25)

        found = False
        for event_data in storage_writer.GetAttributeContainers('event_data'):
            print('Key:', event_data.key)
            print('Timestamp:', event_data.timestamp)
            print('-----')
            if hasattr(event_data,'key') and event_data.key == 'XPCActivityLastAttemptDate.com.apple.routined.learnedLocationEngine.train':
                found = True
                break
        self.assertTrue(found,'Key XPCActivityLastAttemptDate.com.apple.routined.learnedLocationEngine.train was not found')


if __name__ == '__main__':
    unittest.main()
