#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox history database plugin."""

from __future__ import unicode_literals

import collections
import unittest

from plaso.formatters import firefox as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import firefox

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class FirefoxHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mozilla Firefox history database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['places.sqlite'])
  def testProcessPriorTo24(self):
    """Tests the Process function on a Firefox History database file."""
    # This is probably version 23 but potentially an older version.
    plugin = firefox.FirefoxHistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['places.sqlite'], plugin)

    # The places.sqlite file contains 205 events (1 page visit,
    # 2 x 91 bookmark records, 2 x 3 bookmark annotations,
    # 2 x 8 bookmark folders).
    # However there are three events that do not have a timestamp
    # so the test file will show 202 extracted events.

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 202)

    events = list(storage_writer.GetEvents())

    # Check the first page visited event.
    event = events[0]

    self.assertEqual(event.data_type, 'firefox:places:page_visited')

    self.CheckTimestamp(event.timestamp, '2011-07-01 11:16:21.371935')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    expected_url = 'http://news.google.com/'
    self.assertEqual(event.url, expected_url)

    expected_title = 'Google News'
    self.assertEqual(event.title, expected_title)

    expected_message = (
        '{0:s} ({1:s}) [count: 1] Host: news.google.com '
        '(URL not typed directly) Transition: TYPED').format(
            expected_url, expected_title)
    expected_short_message = 'URL: {0:s}'.format(expected_url)

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check the first bookmark event.
    event = events[1]

    self.assertEqual(event.data_type, 'firefox:places:bookmark')

    self.CheckTimestamp(event.timestamp, '2011-07-01 11:13:59.266344')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    # Check the second bookmark event.
    event = events[2]

    self.assertEqual(event.data_type, 'firefox:places:bookmark')

    self.CheckTimestamp(event.timestamp, '2011-07-01 11:13:59.267198')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    expected_url = (
        'place:folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder=TOOLBAR&'
        'sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation=livemark%2F'
        'feedURI&maxResults=10&queryType=1')
    self.assertEqual(event.url, expected_url)

    expected_title = 'Recently Bookmarked'
    self.assertEqual(event.title, expected_title)

    expected_message = (
        'Bookmark URL {0:s} ({1:s}) [folder=BOOKMARKS_MENU&'
        'folder=UNFILED_BOOKMARKS&folder=TOOLBAR&sort=12&excludeQueries=1&'
        'excludeItemIfParentHasAnnotation=livemark%2FfeedURI&maxResults=10&'
        'queryType=1] visit count 0').format(
            expected_title, expected_url)
    expected_short_message = (
        'Bookmarked Recently Bookmarked '
        '(place:folder=BOOKMARKS_MENU&folder=UNFILED_BO...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check the first bookmark annotation event.
    event = events[183]

    self.assertEqual(
        event.data_type, 'firefox:places:bookmark_annotation')

    self.CheckTimestamp(event.timestamp, '2011-07-01 11:13:59.267146')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    # Check another bookmark annotation event.
    event = events[184]

    self.assertEqual(
        event.data_type, 'firefox:places:bookmark_annotation')

    self.CheckTimestamp(event.timestamp, '2011-07-01 11:13:59.267605')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_url = 'place:sort=14&type=6&maxResults=10&queryType=1'
    self.assertEqual(event.url, expected_url)

    expected_title = 'Recent Tags'
    self.assertEqual(event.title, expected_title)

    expected_message = (
        'Bookmark Annotation: [RecentTags] to bookmark '
        '[{0:s}] ({1:s})').format(
            expected_title, expected_url)
    expected_short_message = 'Bookmark Annotation: Recent Tags'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check the second last bookmark folder event.
    event = events[200]

    self.assertEqual(event.data_type, 'firefox:places:bookmark_folder')

    self.CheckTimestamp(event.timestamp, '2011-03-21 10:05:01.553774')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    # Check the last bookmark folder event.
    event = events[201]

    self.assertEqual(
        event.data_type, 'firefox:places:bookmark_folder')

    self.CheckTimestamp(event.timestamp, '2011-07-01 11:14:11.766851')
    self.assertEqual(
        event.timestamp_desc,
        definitions.TIME_DESCRIPTION_MODIFICATION)

    expected_title = 'Latest Headlines'
    self.assertEqual(event.title, expected_title)

    expected_message = expected_title
    expected_short_message = expected_title
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['places_new.sqlite'])
  def testProcessVersion25(self):
    """Tests the Process function on a Firefox History database file v 25."""
    plugin = firefox.FirefoxHistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['places_new.sqlite'], plugin)

    # The places.sqlite file contains 84 events:
    #     34 page visits.
    #     28 bookmarks
    #     14 bookmark folders
    #     8 annotations

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 84)

    events = list(storage_writer.GetEvents())

    counter = collections.Counter()
    for event in events:
      counter[event.data_type] += 1

    self.assertEqual(counter['firefox:places:bookmark'], 28)
    self.assertEqual(counter['firefox:places:page_visited'], 34)
    self.assertEqual(counter['firefox:places:bookmark_folder'], 14)
    self.assertEqual(counter['firefox:places:bookmark_annotation'], 8)

    event = events[10]

    self.CheckTimestamp(event.timestamp, '2013-10-30 21:57:11.281942')

    expected_message = (
        'http://code.google.com/p/plaso [count: 1] Host: code.google.com '
        '(URL not typed directly) Transition: TYPED')
    expected_short_message = 'URL: http://code.google.com/p/plaso'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


class FirefoxDownloadsPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mozilla Firefox downloads database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['downloads.sqlite'])
  def testProcessVersion25(self):
    """Tests the Process function on a Firefox Downloads database file."""
    plugin = firefox.FirefoxDownloadsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['downloads.sqlite'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # Check the first page visited event.
    event = events[0]

    self.assertEqual(event.data_type, 'firefox:downloads:download')

    self.CheckTimestamp(event.timestamp, '2013-07-18 18:59:59.312000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_START)

    expected_url = (
        'https://plaso.googlecode.com/files/'
        'plaso-static-1.0.1-win32-vs2008.zip')
    self.assertEqual(event.url, expected_url)

    expected_full_path = 'file:///D:/plaso-static-1.0.1-win32-vs2008.zip'
    self.assertEqual(event.full_path, expected_full_path)

    self.assertEqual(event.received_bytes, 15974599)
    self.assertEqual(event.total_bytes, 15974599)


if __name__ == '__main__':
  unittest.main()
