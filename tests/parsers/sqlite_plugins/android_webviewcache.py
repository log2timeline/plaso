#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache plugin."""

import unittest

from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_webviewcache

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class AndroidWebViewCache(test_lib.SQLitePluginTestCase):
  """Tests for the Android WebViewCache database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'webviewCache.db'])
  def testProcess(self):
    """Test the Process function on a WebViewCache file."""
    plugin_object = android_webviewcache.WebViewCachePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'webviewCache.db'], plugin_object)

    self.assertEqual(10, len(storage_writer.events))

    test_event = storage_writer.events[0]
    self.assertEqual(1821, test_event.content_length)
    expected_url = (u'https://apps.skypeassets.com/static/'
                    u'skype.skypeloginstatic/css/print.css?_version=1.15')
    self.assertEqual(expected_url, test_event.url)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-28 09:48:18')
    self.assertEqual(test_event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
