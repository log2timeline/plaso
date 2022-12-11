#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Safari history database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import safari

from tests.parsers.sqlite_plugins import test_lib


class SafariHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Safari History database plugin."""

  def testProcess(self):
    """Tests the process function on a Safari History.db database file."""
    plugin = safari.SafariHistoryPluginSqlite()
    storage_writer = self._ParseDatabaseFileWithPlugin(['History.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'safari:history:visit_sqlite',
        'last_visited_time': '2017-11-09T21:24:28.829571+00:00',
        'title': None,
        'url': 'http://facebook.com/',
        'visit_count': 2,
        'was_http_non_get': False}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
