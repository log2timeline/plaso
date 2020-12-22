#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache plugin."""

from __future__ import unicode_literals

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

    expected_url = (
        'https://apps.skypeassets.com/static/'
        'skype.skypeloginstatic/css/print.css?_version=1.15')

    expected_event_values = {
        'content_length': 1821,
        'timestamp': '2013-03-28 09:48:18.000000',
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'URL: {0:s} '
        'Content Length: 1821').format(expected_url)
    expected_short_message = '{0:s}...'.format(expected_url[:77])

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
