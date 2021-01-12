#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_webviewcache

from tests.parsers.sqlite_plugins import test_lib


class AndroidWebViewCache(test_lib.SQLitePluginTestCase):
  """Tests for the Android WebViewCache database plugin."""

  def testProcess(self):
    """Test the Process function on a WebViewCache file."""
    plugin = android_webviewcache.AndroidWebViewCachePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['webviewCache.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'android:webviewcache',
        'content_length': 1821,
        'timestamp': '2013-03-28 09:48:18.000000',
        'url': (
            'https://apps.skypeassets.com/static/skype.skypeloginstatic/css/'
            'print.css?_version=1.15')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
