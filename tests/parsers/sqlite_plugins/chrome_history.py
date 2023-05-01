#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome History database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import chrome_history

from tests.parsers.sqlite_plugins import test_lib


class GoogleChrome8HistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome 8 history SQLite database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome History database file."""
    plugin = chrome_history.GoogleChrome8HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 71)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the first page visited entry.
    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'last_visited_time': '2011-04-07T12:03:11.000000+00:00',
        'page_transition_type': 0,
        'title': 'Ubuntu Start Page',
        'typed_count': 0,
        'url': 'http://start.ubuntu.com/10.04/Google/',
        'visit_count': 4,
        'visit_source': 3}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check the first file downloaded entry.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'end_time': None,
        'full_path': '/home/john/Downloads/funcats_scr.exe',
        'received_bytes': 1132155,
        'start_time': '2011-05-23T08:35:30+00:00',
        'total_bytes': 1132155,
        'url': 'http://fatloss4idiotsx.com/download/funcats/funcats_scr.exe'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 69)
    self.CheckEventData(event_data, expected_event_values)


class GoogleChrome27HistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome 27 history SQLite database plugin."""

  def testProcess57(self):
    """Tests the Process function on a Google Chrome 57 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-57.0.2987.133'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the page visit entry.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'last_visited_time': '2018-01-21T14:09:53.885478+00:00',
        'title': '',
        'typed_count': 0,
        'visit_count': 1,
        'url': expected_url}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check the file downloaded entry.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'end_time': '2018-01-21T14:09:54.858738+00:00',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'start_time': '2018-01-21T14:09:53.900399+00:00',
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcess58(self):
    """Tests the Process function on a Google Chrome 58 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-58.0.3029.96'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the page visit entry.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'last_visited_time': '2018-01-21T14:09:27.315765+00:00',
        'title': '',
        'typed_count': 0,
        'visit_count': 1,
        'url': expected_url}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check the file downloaded entry.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'end_time': '2018-01-21T14:09:28.116062+00:00',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'start_time': '2018-01-21T14:09:27.200398+00:00',
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcess59(self):
    """Tests the Process function on a Google Chrome 59 History database."""
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-59.0.3071.86'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the page visit entry.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'last_visited_time': '2018-01-21T14:08:52.037692+00:00',
        'title': '',
        'typed_count': 0,
        'visit_count': 1,
        'url': expected_url}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check the file downloaded entry.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'end_time': '2018-01-21T14:08:52.662377+00:00',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'start_time': '2018-01-21T14:08:51.811123+00:00',
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcess59ExtraColumn(self):
    """Tests the Process function on a Google Chrome 59 History database,
    manually modified to have an unexpected column.
    """
    plugin = chrome_history.GoogleChrome27HistoryPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History-59_added-fake-column'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check the page visit entry.
    expected_url = (
        'https://raw.githubusercontent.com/dfirlabs/chrome-specimens/master/'
        'generate-specimens.sh')

    expected_event_values = {
        'data_type': 'chrome:history:page_visited',
        'last_visited_time': '2018-01-21T14:08:52.037692+00:00',
        'title': '',
        'typed_count': 0,
        'visit_count': 1,
        'url': expected_url}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check the file downloaded entry.
    expected_event_values = {
        'data_type': 'chrome:history:file_downloaded',
        'end_time': '2018-01-21T14:08:52.662377+00:00',
        'full_path': '/home/ubuntu/Downloads/plaso-20171231.1.win32.msi',
        'received_bytes': 3080192,
        'start_time': '2018-01-21T14:08:51.811123+00:00',
        'total_bytes': 3080192,
        'url': (
            'https://raw.githubusercontent.com/log2timeline/l2tbinaries/master/'
            'win32/plaso-20171231.1.win32.msi')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
