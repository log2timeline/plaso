#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache plugin."""
import unittest

from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_webviewcache

from tests.parsers.sqlite_plugins import test_lib

class AndroidWebViewCache(test_lib.SQLitePluginTestCase):
  """Tests for the Android WebViewCache database plugin."""

  def testProcess(self):
    """Test the Process function on a WebViewCache file."""
    test_file = self._GetTestFilePath([u'webviewCache.db'])
    plugin = android_webviewcache.WebViewCachePlugin()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    test_event = event_objects[0]
    self.assertEqual(1821, test_event.content_length)
    expected_url = (u'https://apps.skypeassets.com/static/'
                    u'skype.skypeloginstatic/css/print.css?_version=1.15')
    self.assertEqual(expected_url, test_event.url)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-28 09:48:18')
    self.assertEqual(test_event.timestamp, expected_timestamp)


    self.assertEqual(10, len(event_objects))


if __name__ == '__main__':
  unittest.main()
