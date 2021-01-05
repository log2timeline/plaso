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
    plugin = android_webview.WebViewPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['webview.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'cookie_name': 'SC',
        'data': (
            'CC=:CCY=:LC=en-us:LIM=:TM=1362495731:TS=1362495680:TZ=:VAT=:VER='),
        'host': 'skype.com',
        'timestamp': '2014-03-05 15:04:44.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Host: skype.com '
        'Path: / '
        'Secure: False')
    expected_message_short = 'skype.com'

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
