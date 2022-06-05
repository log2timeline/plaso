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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 72)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_events_values = {
        'accessor_identifier': 'com.apple.mobileslideshow',
        'accessor_identifier_type': 'bundleID',
        'resource_category': 'photos',
        'resource_identifier': '0E0134C2-8E0C-40AD-8620-099F6D9C0BEB',
        'timestamp': '2022-04-27 14:53:24.555000'}
    self.CheckEventValues(storage_writer, events[0], expected_events_values)

    expected_events_values = {
        'bundle_identifier': 'com.apple.mobilecal',
        'domain': 'calendars.icloud.com',
        'timestamp': '2022-04-27 14:59:33.170000'}
    self.CheckEventValues(storage_writer, events[8], expected_events_values)


if __name__ == '__main__':
  unittest.main()
