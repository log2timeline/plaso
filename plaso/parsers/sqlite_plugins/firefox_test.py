#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox history database plugin."""

import collections
import unittest

from plaso.formatters import firefox as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import firefox
from plaso.parsers.sqlite_plugins import test_lib


class FirefoxHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mozilla Firefox history database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = firefox.FirefoxHistoryPlugin()

  def testProcessPriorTo24(self):
    """Tests the Process function on a Firefox History database file."""
    # This is probably version 23 but potentially an older version.
    test_file = self._GetTestFilePath([u'places.sqlite'])
    cache = sqlite.SQLiteCache()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The places.sqlite file contains 205 events (1 page visit,
    # 2 x 91 bookmark records, 2 x 3 bookmark annotations,
    # 2 x 8 bookmark folders).
    # However there are three events that do not have a timestamp
    # so the test file will show 202 extracted events.
    self.assertEqual(len(event_objects), 202)

    # Check the first page visited event.
    event_object = event_objects[0]

    self.assertEqual(event_object.data_type, u'firefox:places:page_visited')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.PAGE_VISITED)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-01 11:16:21.371935')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_url = u'http://news.google.com/'
    self.assertEqual(event_object.url, expected_url)

    expected_title = u'Google News'
    self.assertEqual(event_object.title, expected_title)

    expected_msg = (
        u'{0:s} ({1:s}) [count: 1] Host: news.google.com '
        u'(URL not typed directly) Transition: TYPED').format(
            expected_url, expected_title)
    expected_short = u'URL: {0:s}'.format(expected_url)

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # Check the first bookmark event.
    event_object = event_objects[1]

    self.assertEqual(event_object.data_type, u'firefox:places:bookmark')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ADDED_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-01 11:13:59.266344')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Check the second bookmark event.
    event_object = event_objects[2]

    self.assertEqual(event_object.data_type, u'firefox:places:bookmark')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-01 11:13:59.267198')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_url = (
        u'place:folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder=TOOLBAR&'
        u'sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation=livemark%2F'
        u'feedURI&maxResults=10&queryType=1')
    self.assertEqual(event_object.url, expected_url)

    expected_title = u'Recently Bookmarked'
    self.assertEqual(event_object.title, expected_title)

    expected_msg = (
        u'Bookmark URL {0:s} ({1:s}) [folder=BOOKMARKS_MENU&'
        u'folder=UNFILED_BOOKMARKS&folder=TOOLBAR&sort=12&excludeQueries=1&'
        u'excludeItemIfParentHasAnnotation=livemark%2FfeedURI&maxResults=10&'
        u'queryType=1] visit count 0').format(
            expected_title, expected_url)
    expected_short = (
        u'Bookmarked Recently Bookmarked '
        u'(place:folder=BOOKMARKS_MENU&folder=UNFILED_BO...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # Check the first bookmark annotation event.
    event_object = event_objects[183]

    self.assertEqual(
        event_object.data_type, u'firefox:places:bookmark_annotation')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-01 11:13:59.267146')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Check another bookmark annotation event.
    event_object = event_objects[184]

    self.assertEqual(
        event_object.data_type, u'firefox:places:bookmark_annotation')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-01 11:13:59.267605')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_url = u'place:sort=14&type=6&maxResults=10&queryType=1'
    self.assertEqual(event_object.url, expected_url)

    expected_title = u'Recent Tags'
    self.assertEqual(event_object.title, expected_title)

    expected_msg = (
        u'Bookmark Annotation: [RecentTags] to bookmark '
        u'[{0:s}] ({1:s})').format(
            expected_title, expected_url)
    expected_short = u'Bookmark Annotation: Recent Tags'
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # Check the second last bookmark folder event.
    event_object = event_objects[200]

    self.assertEqual(event_object.data_type, u'firefox:places:bookmark_folder')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ADDED_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-03-21 10:05:01.553774')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    # Check the last bookmark folder event.
    event_object = event_objects[201]

    self.assertEqual(
        event_object.data_type, u'firefox:places:bookmark_folder')

    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-01 11:14:11.766851')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_title = u'Latest Headlines'
    self.assertEqual(event_object.title, expected_title)

    expected_msg = expected_title
    expected_short = expected_title
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

  def testProcessVersion25(self):
    """Tests the Process function on a Firefox History database file v 25."""
    test_file = self._GetTestFilePath([u'places_new.sqlite'])
    cache = sqlite.SQLiteCache()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The places.sqlite file contains 84 events:
    #     34 page visits.
    #     28 bookmarks
    #     14 bookmark folders
    #     8 annotations
    self.assertEqual(len(event_objects), 84)
    counter = collections.Counter()
    for event_object in event_objects:
      counter[event_object.data_type] += 1

    self.assertEqual(counter[u'firefox:places:bookmark'], 28)
    self.assertEqual(counter[u'firefox:places:page_visited'], 34)
    self.assertEqual(counter[u'firefox:places:bookmark_folder'], 14)
    self.assertEqual(counter[u'firefox:places:bookmark_annotation'], 8)

    random_event = event_objects[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-30 21:57:11.281942')
    self.assertEqual(random_event.timestamp, expected_timestamp)

    expected_short = u'URL: http://code.google.com/p/plaso'
    expected_msg = (
        u'http://code.google.com/p/plaso [count: 1] Host: code.google.com '
        u'(URL not typed directly) Transition: TYPED')

    self._TestGetMessageStrings(random_event, expected_msg, expected_short)


class FirefoxDownloadsPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mozilla Firefox downloads database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = firefox.FirefoxDownloadsPlugin()

  def testProcessVersion25(self):
    """Tests the Process function on a Firefox Downloads database file."""
    test_file = self._GetTestFilePath([u'downloads.sqlite'])
    cache = sqlite.SQLiteCache()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The downloads.sqlite file contains 2 events (1 download).
    self.assertEqual(len(event_objects), 2)

    # Check the first page visited event.
    event_object = event_objects[0]

    self.assertEqual(event_object.data_type, u'firefox:downloads:download')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.START_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-18 18:59:59.312000')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_url = (
        u'https://plaso.googlecode.com/files/'
        u'plaso-static-1.0.1-win32-vs2008.zip')
    self.assertEqual(event_object.url, expected_url)

    expected_full_path = u'file:///D:/plaso-static-1.0.1-win32-vs2008.zip'
    self.assertEqual(event_object.full_path, expected_full_path)

    self.assertEqual(event_object.received_bytes, 15974599)
    self.assertEqual(event_object.total_bytes, 15974599)


if __name__ == '__main__':
  unittest.main()
