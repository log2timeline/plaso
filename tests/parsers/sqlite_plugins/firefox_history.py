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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 202)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the first page visited event.
    expected_event_values = {
        'data_type': 'firefox:places:page_visited',
        'date_time': '2011-07-01 11:16:21.371935',
        'host': 'news.google.com',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': 'Google News',
        'url': 'http://news.google.com/',
        'visit_count': 1,
        'visit_type': 2}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Check the first bookmark event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark',
        'date_time': '2011-07-01 11:13:59.266344',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Check the second bookmark event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark',
        'date_time': '2011-07-01 11:13:59.267198',
        'places_title': (
            'folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder=TOOLBAR&'
            'sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation=livemark'
            '%2FfeedURI&maxResults=10&queryType=1'),
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'title': 'Recently Bookmarked',
        'type': 'URL',
        'url': (
            'place:folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder='
            'TOOLBAR&sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation='
            'livemark%2FfeedURI&maxResults=10&queryType=1'),
        'visit_count': 0}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Check the first bookmark annotation event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark_annotation',
        'date_time': '2011-07-01 11:13:59.267146',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[183], expected_event_values)

    # Check another bookmark annotation event.
    expected_event_values = {
        'content': 'RecentTags',
        'data_type': 'firefox:places:bookmark_annotation',
        'date_time': '2011-07-01 11:13:59.267605',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED,
        'title': 'Recent Tags',
        'url': 'place:sort=14&type=6&maxResults=10&queryType=1'}

    self.CheckEventValues(storage_writer, events[184], expected_event_values)

    # Check the second last bookmark folder event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark_folder',
        'date_time': '2011-03-21 10:05:01.553774',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[200], expected_event_values)

    # Check the last bookmark folder event.
    expected_event_values = {
        'data_type': 'firefox:places:bookmark_folder',
        'date_time': '2011-07-01 11:14:11.766851',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'title': 'Latest Headlines'}

    self.CheckEventValues(storage_writer, events[201], expected_event_values)

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 84)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

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
        'data_type': 'firefox:places:page_visited',
        'date_time': '2013-10-30 21:57:11.281942',
        'host': 'code.google.com',
        'url': 'http://code.google.com/p/plaso',
        'visit_count': 1,
        'visit_type': 2}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)


if __name__ == '__main__':
  unittest.main()
