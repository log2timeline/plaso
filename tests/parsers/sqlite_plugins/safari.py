#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Safari history database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import safari as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import safari

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class SafariHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Safari History database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['History.db'])
  def testProcess(self):
    """Tests the process function on a Safari History.db database file."""
    plugin = safari.SafariHistoryPluginSqlite()
    storage_writer = self._ParseDatabaseFileWithPlugin(['History.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 25)

    events = list(storage_writer.GetEvents())

    # Check the first page visited entry
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2017-11-09 21:24:28.829571')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    expected_url = 'http://facebook.com/'
    self.assertEqual(event.url, expected_url)

    expected_title = ''
    self.assertEqual(event.title, expected_title)

    expected_message = (
        'URL: {0:s} [count: 2] http_non_get: False').format(expected_url)

    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
