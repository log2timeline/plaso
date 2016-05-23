#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android WebView plugin."""

import unittest

from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_webview

from tests.parsers.sqlite_plugins import test_lib


class AndroidWebView(test_lib.SQLitePluginTestCase):
  """Tests for the AndroidWebView database plugin."""

  def testProcess(self):
    """Test the Process function on a WebView SQLite file."""
    test_file = self._GetTestFilePath([u'webview.db'])
    plugin = android_webview.WebViewPlugin()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    test_event = event_objects[0]
    self.assertEqual(test_event.host, u'.skype.com')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-03-05 15:04:44')
    self.assertEqual(test_event.timestamp, expected_timestamp)
    self.assertEqual(test_event.cookie_name, u'SC')
    expected_data = (
        u'CC=:CCY=:LC=en-us:LIM=:TM=1362495731:TS=1362495680:TZ=:VAT=:VER=')
    self.assertEqual(test_event.data, expected_data)

    self.assertEqual(len(event_objects), 3)


if __name__ == '__main__':
  unittest.main()
