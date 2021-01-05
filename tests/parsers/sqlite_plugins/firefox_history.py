#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox history database plugin."""

import collections
import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import firefox_history

from tests.parsers.sqlite_plugins import test_lib


class FirefoxHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mozilla Firefox history database plugin."""

  def testProcessPriorTo24(self):
    """Tests the Process function on a Firefox History database file."""
    # This is probably version 23 but potentially an older version.
    plugin = firefox_history.FirefoxHistoryPlugin()
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
    expected_title = 'Google News'
    expected_url = 'http://news.google.com/'

    expected_event_values = {
        'data_type': 'firefox:places:page_visited',
        'timestamp': '2011-07-01 11:16:21.371935',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': expected_title,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        '{0:s} ({1:s}) [count: 1] Host: news.google.com '
        '(URL not typed directly) Transition: TYPED').format(
            expected_url, expected_title)
    expected_short_message = 'URL: {0:s}'.format(expected_url)

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the first bookmark event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark',
        'timestamp': '2011-07-01 11:13:59.266344',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Check the second bookmark event.
    expected_title = 'Recently Bookmarked'
    expected_url = (
        'place:folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder=TOOLBAR&'
        'sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation=livemark%2F'
        'feedURI&maxResults=10&queryType=1')

    expected_event_values = {
        'data_type': 'firefox:places:bookmark',
        'timestamp': '2011-07-01 11:13:59.267198',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'title': expected_title,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_message = (
        'Bookmark URL {0:s} ({1:s}) [folder=BOOKMARKS_MENU&'
        'folder=UNFILED_BOOKMARKS&folder=TOOLBAR&sort=12&excludeQueries=1&'
        'excludeItemIfParentHasAnnotation=livemark%2FfeedURI&maxResults=10&'
        'queryType=1] visit count 0').format(
            expected_title, expected_url)
    expected_short_message = (
        'Bookmarked Recently Bookmarked '
        '(place:folder=BOOKMARKS_MENU&folder=UNFILED_BO...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[2])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the first bookmark annotation event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark_annotation',
        'timestamp': '2011-07-01 11:13:59.267146',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[183], expected_event_values)

    # Check another bookmark annotation event.
    expected_title = 'Recent Tags'
    expected_url = 'place:sort=14&type=6&maxResults=10&queryType=1'

    expected_event_values = {
        'data_type': 'firefox:places:bookmark_annotation',
        'timestamp': '2011-07-01 11:13:59.267605',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED,
        'title': expected_title,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[184], expected_event_values)

    expected_message = (
        'Bookmark Annotation: [RecentTags] to bookmark '
        '[{0:s}] ({1:s})').format(expected_title, expected_url)
    expected_short_message = 'Bookmark Annotation: Recent Tags'

    event_data = self._GetEventDataOfEvent(storage_writer, events[184])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the second last bookmark folder event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark_folder',
        'timestamp': '2011-03-21 10:05:01.553774',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[200], expected_event_values)

    # Check the last bookmark folder event.
    expected_title = 'Latest Headlines'

    expected_event_values = {
        'data_type': 'firefox:places:bookmark_folder',
        'timestamp': '2011-07-01 11:14:11.766851',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'title': expected_title}

    self.CheckEventValues(storage_writer, events[201], expected_event_values)

    expected_message = expected_title
    expected_short_message = expected_title

    event_data = self._GetEventDataOfEvent(storage_writer, events[201])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testProcessVersion25(self):
    """Tests the Process function on a Firefox History database file v 25."""
    plugin = firefox_history.FirefoxHistoryPlugin()
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
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      counter[event_data.data_type] += 1

    self.assertEqual(counter['firefox:places:bookmark'], 28)
    self.assertEqual(counter['firefox:places:page_visited'], 34)
    self.assertEqual(counter['firefox:places:bookmark_folder'], 14)
    self.assertEqual(counter['firefox:places:bookmark_annotation'], 8)

    expected_event_values = {
        'timestamp': '2013-10-30 21:57:11.281942'}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)

    expected_message = (
        'http://code.google.com/p/plaso [count: 1] Host: code.google.com '
        '(URL not typed directly) Transition: TYPED')
    expected_short_message = 'URL: http://code.google.com/p/plaso'

    event_data = self._GetEventDataOfEvent(storage_writer, events[10])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
