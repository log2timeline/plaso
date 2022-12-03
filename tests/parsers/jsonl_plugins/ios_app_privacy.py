# -*- coding: utf-8 -*
"""Tests for the JSON-L parser plugin for iOS application privacy reports."""

import unittest

from plaso.parsers.jsonl_plugins import ios_app_privacy

from tests.parsers.jsonl_plugins import test_lib


class IOSAppPrivacPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for iOS application privacy reports."""

  def testProcess(self):
    """Tests for the Process function"""
    plugin = ios_app_privacy.IOSAppPrivacPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin([
        'ios_app_privacy_report.ndjson'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 72)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test access event data.
    expected_event_values = {
        'accessor_identifier': 'com.apple.mobileslideshow',
        'accessor_identifier_type': 'bundleID',
        'data_type': 'ios:app_privacy:access',
        'recorded_time': '2022-04-27T10:53:24.555000-04:00',
        'resource_category': 'photos',
        'resource_identifier': '0E0134C2-8E0C-40AD-8620-099F6D9C0BEB'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test network activity event data.
    expected_event_values = {
        'bundle_identifier': 'com.apple.mobilecal',
        'data_type': 'ios:app_privacy:network',
        'domain': 'calendars.icloud.com',
        'recorded_time': '2022-04-27T10:59:33.170000-04:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
