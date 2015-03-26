#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome History database plugin."""

import unittest

from plaso.formatters import chrome as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import chrome
from plaso.parsers.sqlite_plugins import test_lib


class ChromeHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome History database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = chrome.ChromeHistoryPlugin()

  def testProcess(self):
    """Tests the Process function on a Chrome History database file."""
    test_file = self._GetTestFilePath([u'History'])
    cache = sqlite.SQLiteCache()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The History file contains 71 events (69 page visits, 1 file downloads).
    self.assertEqual(len(event_objects), 71)

    # Check the first page visited entry.
    event_object = event_objects[0]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.PAGE_VISITED)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-04-07 12:03:11')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_url = u'http://start.ubuntu.com/10.04/Google/'
    self.assertEqual(event_object.url, expected_url)

    expected_title = u'Ubuntu Start Page'
    self.assertEqual(event_object.title, expected_title)

    expected_msg = (
        u'{0:s} ({1:s}) [count: 0] Host: start.ubuntu.com '
        u'Visit Source: [SOURCE_FIREFOX_IMPORTED] Type: [LINK - User clicked '
        u'a link] (URL not typed directly - no typed count)').format(
            expected_url, expected_title)
    expected_short = u'{0:s} ({1:s})'.format(expected_url, expected_title)

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # Check the first file downloaded entry.
    event_object = event_objects[69]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.FILE_DOWNLOADED)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-05-23 08:35:30')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_url = (
        u'http://fatloss4idiotsx.com/download/funcats/'
        u'funcats_scr.exe')
    self.assertEqual(event_object.url, expected_url)

    expected_full_path = u'/home/john/Downloads/funcats_scr.exe'
    self.assertEqual(event_object.full_path, expected_full_path)

    expected_msg = (
        u'{0:s} ({1:s}). '
        u'Received: 1132155 bytes out of: '
        u'1132155 bytes.').format(expected_url, expected_full_path)
    expected_short = u'{0:s} downloaded (1132155 bytes)'.format(
        expected_full_path)
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
