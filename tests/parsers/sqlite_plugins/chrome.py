#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome History database plugin."""

import unittest

from plaso.formatters import chrome  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import chrome

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class ChromeHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome History database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'History'])
  def testProcess(self):
    """Tests the Process function on a Chrome History database file."""
    plugin = chrome.ChromeHistoryPlugin()
    cache = sqlite.SQLiteCache()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'History'], plugin, cache=cache)

    # The History file contains 71 events (69 page visits, 1 file downloads).
    self.assertEqual(storage_writer.number_of_events, 71)

    events = list(storage_writer.GetEvents())

    # Check the first page visited entry.
    event = events[0]

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-04-07 12:03:11')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_url = u'http://start.ubuntu.com/10.04/Google/'
    self.assertEqual(event.url, expected_url)

    expected_title = u'Ubuntu Start Page'
    self.assertEqual(event.title, expected_title)

    expected_message = (
        u'{0:s} ({1:s}) [count: 0] Host: start.ubuntu.com '
        u'Visit Source: [SOURCE_FIREFOX_IMPORTED] Type: [LINK - User clicked '
        u'a link] (URL not typed directly - no typed count)').format(
            expected_url, expected_title)
    expected_short_message = u'{0:s} ({1:s})'.format(
        expected_url, expected_title)

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check the first file downloaded entry.
    event = events[69]

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-05-23 08:35:30')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_url = (
        u'http://fatloss4idiotsx.com/download/funcats/'
        u'funcats_scr.exe')
    self.assertEqual(event.url, expected_url)

    expected_full_path = u'/home/john/Downloads/funcats_scr.exe'
    self.assertEqual(event.full_path, expected_full_path)

    expected_message = (
        u'{0:s} ({1:s}). '
        u'Received: 1132155 bytes out of: '
        u'1132155 bytes.').format(expected_url, expected_full_path)
    expected_short_message = u'{0:s} downloaded (1132155 bytes)'.format(
        expected_full_path)
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
