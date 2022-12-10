#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android WebView plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_webview

from tests.parsers.sqlite_plugins import test_lib


class AndroidWebView(test_lib.SQLitePluginTestCase):
  """Tests for the AndroidWebView database plugin."""

  def testProcess(self):
    """Test the Process function on a WebView SQLite file."""
    plugin = android_webview.AndroidWebViewPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['webview.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'cookie_name': 'SC',
        'data': (
            'CC=:CCY=:LC=en-us:LIM=:TM=1362495731:TS=1362495680:TZ=:VAT=:VER='),
        'data_type': 'android:webview:cookie',
        'expiration_time': '2014-03-05T15:04:44.000+00:00',
        'host': 'skype.com',
        'path': '/',
        'secure': False}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
