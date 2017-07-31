#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache plugin."""

import unittest

from plaso.formatters import android_webviewcache  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import android_webviewcache

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class AndroidWebViewCache(test_lib.SQLitePluginTestCase):
  """Tests for the Android WebViewCache database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'webviewCache.db'])
  def testProcess(self):
    """Test the Process function on a WebViewCache file."""
    plugin = android_webviewcache.AndroidWebViewCachePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'webviewCache.db'], plugin)

    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-03-28 09:48:18')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(1821, event.content_length)

    expected_url = (
        u'https://apps.skypeassets.com/static/'
        u'skype.skypeloginstatic/css/print.css?_version=1.15')
    self.assertEqual(expected_url, event.url)

    expected_message = (
        u'URL: {0:s} '
        u'Content Length: 1821').format(expected_url)
    expected_short_message = u'{0:s}...'.format(expected_url[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
