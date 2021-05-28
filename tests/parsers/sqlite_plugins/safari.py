#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Safari history database plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import safari

from tests.parsers.sqlite_plugins import test_lib


class SafariHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Safari History database plugin."""

  def testProcess(self):
    """Tests the process function on a Safari History.db database file."""
    plugin = safari.SafariHistoryPluginSqlite()
    storage_writer = self._ParseDatabaseFileWithPlugin(['History.db'], plugin)

    self.assertEqual(storage_writer.number_of_events, 25)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'safari:history:visit_sqlite',
        'date_time': '2017-11-09 21:24:28.829571',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'title': '',
        'url': 'http://facebook.com/',
        'visit_count': 2,
        'was_http_non_get': False}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
