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

    # The History file contains 71 events (69 page visits, 1 file downloads).
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 71)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the first page visited entry.
    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'date_time': '2011-04-07 12:03:11.000000',
        'page_transition_type': 0,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': 'Ubuntu Start Page',
        'typed_count': 0,
        'url': 'http://start.ubuntu.com/10.04/Google/',
        'visit_source': 3}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Check the first file downloaded entry.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'date_time': '2011-05-23 08:35:30',
        'full_path': '/home/john/Downloads/funcats_scr.exe',
        'received_bytes': 1132155,
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'total_bytes': 1132155,
        'url': 'http://fatloss4idiotsx.com/download/funcats/funcats_scr.exe'}

    self.CheckEventValues(storage_writer, events[69], expected_event_values)


class GoogleChrome27HistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome 27 history SQLite database plugin."""

  def testProcess57(self):
    """Tests the Process function on a Google Chrome 57 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-57.0.2987.133'], plugin)

    # The History file contains 3 events (1 page visit, 2 file downloads).
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'date_time': '2018-01-21 14:09:53.885478',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'typed_count': 0,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Check the file downloaded event.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'date_time': '2018-01-21 14:09:53.900399',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'timestamp_desc': definitions.TIME_DESCRIPTION_START,
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

  def testProcess58(self):
    """Tests the Process function on a Google Chrome 58 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-58.0.3029.96'], plugin)

    # The History file contains 3 events (1 page visit, 2 file downloads).
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'date_time': '2018-01-21 14:09:27.315765',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'typed_count': 0,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Check the file downloaded event.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'date_time': '2018-01-21 14:09:27.200398',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'timestamp_desc': definitions.TIME_DESCRIPTION_START,
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

  def testProcess59(self):
    """Tests the Process function on a Google Chrome 59 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-59.0.3071.86'], plugin)

    # The History file contains 3 events (1 page visit, 2 file downloads).
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'date_time': '2018-01-21 14:08:52.037692',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'typed_count': 0,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Check the file downloaded event.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'date_time': '2018-01-21 14:08:51.811123',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'timestamp_desc': definitions.TIME_DESCRIPTION_START,
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

  def testProcess59ExtraColumn(self):
    """Tests the Process function on a Google Chrome 59 History database,
    manually modified to have an unexpected column.
    """
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-59_added-fake-column'], plugin)

    # The History file contains 3 events (1 page visit, 2 file downloads).
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the page visit event.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'date_time': '2018-01-21 14:08:52.037692',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'typed_count': 0,
        'url': expected_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Check the file downloaded event.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'date_time': '2018-01-21 14:08:51.811123',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'timestamp_desc': definitions.TIME_DESCRIPTION_START,
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
