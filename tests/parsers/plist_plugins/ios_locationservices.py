import unittest
from plaso.parsers.plist_plugins import ios_locationservices
from tests.parsers.plist_plugins import test_lib

class IOSRoutinedPlistPluginTest(test_lib.PlistPluginTestCase):
    """Tests for the Apple iOS Routined plist plugin."""

    def testProcess(self):
        """Tests the Process function."""
        plist_name = 'com.apple.routined.plist'

        plugin = ios_locationservices.IOSRoutinedPlistPlugin()
        storage_writer = self._ParsePlistFileWithPlugin(
            plugin, [plist_name], plist_name)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            'event_data')
        self.assertGreater(number_of_event_data, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            'extraction_warning')
        self.assertEqual(number_of_warnings, 0)

        number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
            'recovery_warning')
        self.assertEqual(number_of_recovery_warnings, 0)

        expected_event_values = {
            'key': 'XPCActivityLastAttemptDate.com.apple.routined.assets',
            'value': '2023-05-20T01:42:39.602781184+00:00',
            'data_type': 'ios:routined:entry'
        }

        event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
        self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
    unittest.main()
