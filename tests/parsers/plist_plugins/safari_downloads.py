#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Safari Downloads plist plugin."""

import unittest

from plaso.parsers.plist_plugins import safari_downloads

from tests.parsers.plist_plugins import test_lib


class SafariDownloadsPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari Downloads plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'Downloads.plist'

    plugin = safari_downloads.SafariDownloadsPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'safari:downloads:entry',
        'end_time': '2022-12-14T19:05:30.620490+00:00',
        'full_path': (
            '~/Downloads/paint.net.4.3.12.install.anycpu.web.zip.download/'
            'paint.net.4.3.12.install.anycpu.web.zip'),
        'received_bytes': 826337,
        'remove_on_completion': False,
        'start_time': '2022-12-14T19:05:26.862793+00:00',
        'total_bytes': 826337,
        'url': (
            'https://www.dotpdn.com/files/'
            'paint.net.4.3.12.install.anycpu.web.zip')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
