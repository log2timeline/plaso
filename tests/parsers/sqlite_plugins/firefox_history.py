#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox history database plugin."""

import unittest

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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 103)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check a page visited entry.
    expected_event_values = {
        'data_type': 'firefox:places:page_visited',
        'host': 'news.google.com',
        'last_visited_time': '2011-07-01T11:16:21.371935+00:00',
        'title': 'Google News',
        'url': 'http://news.google.com/',
        'visit_count': 1,
        'visit_type': 2}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check a bookmark entry.
    expected_event_values = {
        'added_time': '2011-07-01T11:13:59.266344+00:00',
        'data_type': 'firefox:places:bookmark',
        'modification_time': '2011-07-01T11:13:59.267198+00:00',
        'places_title': (
            'folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder=TOOLBAR&'
            'sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation=livemark'
            '%2FfeedURI&maxResults=10&queryType=1'),
        'type': 'URL',
        'url': (
            'place:folder=BOOKMARKS_MENU&folder=UNFILED_BOOKMARKS&folder='
            'TOOLBAR&sort=12&excludeQueries=1&excludeItemIfParentHasAnnotation='
            'livemark%2FfeedURI&maxResults=10&queryType=1'),
        'visit_count': 0}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Check a bookmark annotation entry.
    expected_event_values = {
        'added_time': '2011-07-01T11:13:59.267605+00:00',
        'content': 'RecentTags',
        'data_type': 'firefox:places:bookmark_annotation',
        'modification_time': None,
        'title': 'Recent Tags',
        'url': 'place:sort=14&type=6&maxResults=10&queryType=1'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 93)
    self.CheckEventData(event_data, expected_event_values)

    # Check a bookmark folder entry.
    expected_event_values = {
        'added_time': '2011-03-21T10:05:01.553774+00:00',
        'data_type': 'firefox:places:bookmark_folder',
        'modification_time': '2011-07-01T11:14:11.766851+00:00',
        'title': 'Latest Headlines'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 102)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessVersion25(self):
    """Tests the Process function on a Firefox History database file v 25."""
    plugin = firefox_history.FirefoxHistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['places_new.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 59)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'firefox:places:page_visited',
        'last_visited_time': '2013-10-30T21:57:11.281942+00:00',
        'host': 'code.google.com',
        'url': 'http://code.google.com/p/plaso',
        'visit_count': 1,
        'visit_type': 2}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 10)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
