#!/usr/bin/env python3
"""Tests for the iOS SIM information plist plugin."""

import unittest

from plaso.parsers.plist_plugins import ios_siminfo
from tests.parsers.plist_plugins import test_lib


class IOSSIMInfoPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the iOS SIM information plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'com.apple.commcenter.data.plist'

    plugin = ios_siminfo.IOSSIMInfoPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, ['ios', plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'cell_broadcast_version': '49.0',
        'data_type': 'ios:sim:info',
        'eap_aka_enabled': True,
        'label_identifier': 'E8B6082D-F391-46CB-9780-0AF46534D89F',
        'last_used_time': '2023-05-17T12:26:22+00:00',
        'phone_number': '+19195794674',
        'sim_type': 'sim'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
