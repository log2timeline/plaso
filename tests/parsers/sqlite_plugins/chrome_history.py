#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome History database plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import chrome_history

from tests.parsers.sqlite_plugins import test_lib


class GoogleChrome8HistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome 8 history SQLite database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome History database file."""
    plugin = chrome_history.GoogleChrome8HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    # The History file contains 71 events (69 page visits, 1 file downloads).
    self.assertEqual(storage_writer.number_of_events, 71)

    events = list(storage_writer.GetEvents())

    # Check the first page visited entry.
    expected_url = 'http://start.ubuntu.com/10.04/Google/'

    expected_event_values = {
        'timestamp': '2011-04-07 12:03:11.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': 'Ubuntu Start Page',
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        '{0:s} '
        '(Ubuntu Start Page) [count: 0] '
        'Visit Source: [SOURCE_FIREFOX_IMPORTED] Type: [LINK - User clicked '
        'a link] (URL not typed directly)').format(
            expected_url)
    expected_short_message = '{0:s} (Ubuntu Start Page)'.format(expected_url)

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the first file downloaded entry.
    expected_full_path = '/home/john/Downloads/funcats_scr.exe'
    expected_url = (
        'http://fatloss4idiotsx.com/download/funcats/'
        'funcats_scr.exe')

    expected_event_values = {
        'full_path': expected_full_path,
        'timestamp': '2011-05-23 08:35:30.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[69], expected_event_values)

    expected_message = (
        '{0:s} ({1:s}). '
        'Received: 1132155 bytes out of: '
        '1132155 bytes.').format(expected_url, expected_full_path)
    expected_short_message = '{0:s} downloaded (1132155 bytes)'.format(
        expected_full_path)

    event_data = self._GetEventDataOfEvent(storage_writer, events[69])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


class GoogleChrome27HistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome 27 history SQLite database plugin."""

  def testProcess57(self):
    """Tests the Process function on a Google Chrome 57 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-57.0.2987.133'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    # The History file contains 2 events (1 page visits, 1 file downloads).
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'timestamp': '2018-01-21 14:09:53.885478',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        '{0:s} '
        '[count: 0] '
        'Type: [START_PAGE - The start page of the browser] '
        '(URL not typed directly)').format(expected_url)
    expected_short_message = '{0:s}...'.format(expected_url[:77])

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the file downloaded event.
    expected_full_path = '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi'
    expected_url = (
        'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
        'win32/plaso-20171231.1.win32.msi')

    expected_event_values = {
        'full_path': expected_full_path,
        'timestamp': '2018-01-21 14:09:53.900399',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_message = (
        '{0:s} ({1:s}). '
        'Received: 3080192 bytes out of: 3080192 bytes.').format(
            expected_url, expected_full_path)
    expected_short_message = '{0:s} downloaded (3080192 bytes)'.format(
        expected_full_path)

    event_data = self._GetEventDataOfEvent(storage_writer, events[1])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testProcess58(self):
    """Tests the Process function on a Google Chrome 58 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-58.0.3029.96'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    # The History file contains 2 events (1 page visits, 1 file downloads).
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'timestamp': '2018-01-21 14:09:27.315765',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        '{0:s} '
        '[count: 0] '
        'Type: [START_PAGE - The start page of the browser] '
        '(URL not typed directly)').format(expected_url)
    expected_short_message = '{0:s}...'.format(expected_url[:77])

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the file downloaded event.
    expected_full_path = '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi'
    expected_url = (
        'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
        'win32/plaso-20171231.1.win32.msi')

    expected_event_values = {
        'full_path': expected_full_path,
        'timestamp': '2018-01-21 14:09:27.200398',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_message = (
        '{0:s} ({1:s}). '
        'Received: 3080192 bytes out of: 3080192 bytes.').format(
            expected_url, expected_full_path)
    expected_short_message = '{0:s} downloaded (3080192 bytes)'.format(
        expected_full_path)

    event_data = self._GetEventDataOfEvent(storage_writer, events[1])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testProcess59(self):
    """Tests the Process function on a Google Chrome 59 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-59.0.3071.86'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    # The History file contains 2 events (1 page visits, 1 file downloads).
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'timestamp': '2018-01-21 14:08:52.037692',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        '{0:s} '
        '[count: 0] '
        'Type: [START_PAGE - The start page of the browser] '
        '(URL not typed directly)').format(expected_url)
    expected_short_message = '{0:s}...'.format(expected_url[:77])

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the file downloaded event.
    expected_full_path = '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi'
    expected_url = (
        'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
        'win32/plaso-20171231.1.win32.msi')

    expected_event_values = {
        'full_path': expected_full_path,
        'timestamp': '2018-01-21 14:08:51.811123',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_message = (
        '{0:s} ({1:s}). '
        'Received: 3080192 bytes out of: 3080192 bytes.').format(
            expected_url, expected_full_path)
    expected_short_message = '{0:s} downloaded (3080192 bytes)'.format(
        expected_full_path)

    event_data = self._GetEventDataOfEvent(storage_writer, events[1])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testProcess59ExtraColumn(self):
    """Tests the Process function on a Google Chrome 59 History database,
    manually modified to have an unexpected column.
    """
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-59_added-fake-column'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    # The History file contains 2 events (1 page visits, 1 file downloads).
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'timestamp': '2018-01-21 14:08:52.037692',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        '{0:s} '
        '[count: 0] '
        'Type: [START_PAGE - The start page of the browser] '
        '(URL not typed directly)').format(expected_url)
    expected_short_message = '{0:s}...'.format(expected_url[:77])

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the file downloaded event.
    expected_full_path = '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi'
    expected_url = (
        'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
        'win32/plaso-20171231.1.win32.msi')

    expected_event_values = {
        'full_path': expected_full_path,
        'timestamp': '2018-01-21 14:08:51.811123',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_message = (
        '{0:s} ({1:s}). '
        'Received: 3080192 bytes out of: 3080192 bytes.').format(
            expected_url, expected_full_path)
    expected_short_message = '{0:s} downloaded (3080192 bytes)'.format(
        expected_full_path)

    event_data = self._GetEventDataOfEvent(storage_writer, events[1])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
