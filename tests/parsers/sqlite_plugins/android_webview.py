#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android WebView plugin."""

import unittest

from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_webview

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class AndroidWebView(test_lib.SQLitePluginTestCase):
  """Tests for the AndroidWebView database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'webview.db'])
  def testProcess(self):
    """Test the Process function on a WebView SQLite file."""
    plugin = android_webview.WebViewPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'webview.db'], plugin)

    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.host, u'skype.com')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-03-05 15:04:44')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.cookie_name, u'SC')
    expected_data = (
        u'CC=:CCY=:LC=en-us:LIM=:TM=1362495731:TS=1362495680:TZ=:VAT=:VER=')
    self.assertEqual(event.data, expected_data)


if __name__ == '__main__':
  unittest.main()
