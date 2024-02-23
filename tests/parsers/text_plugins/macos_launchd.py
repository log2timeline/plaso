#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mac OS launchd log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import macos_launchd

from tests.parsers.text_plugins import test_lib


class MacOSLaunchdLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Mac OS launchd log text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = macos_launchd.MacOSLaunchdLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['macos_launchd.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 36609)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': (
            'launchd logging initialized. name: com.apple.xpc.launchd pid: 1'),
        'severity': 'Notice',
        'written_time': '2023-06-08T14:51:39.068413+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 12)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'body': 'internal event: PETRIFIED, code = 0',
        'process_name': 'pid/1660/com.apple.audio.AUHostingService.arm64e',
        'severity': 'Notice',
        'written_time': '2023-06-08T11:20:20.231350+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', 36603)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
