#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox downloads database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import firefox_downloads

from tests.parsers.sqlite_plugins import test_lib


class FirefoxDownloadsPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mozilla Firefox downloads database plugin."""

  def testProcessVersion25(self):
    """Tests the Process function on a Firefox Downloads database file."""
    plugin = firefox_downloads.FirefoxDownloadsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['downloads.sqlite'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # Check the first page visited event.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-07-18 18:59:59.312000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_START)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'firefox:downloads:download')

    expected_url = (
        'https://plaso.googlecode.com/files/'
        'plaso-static-1.0.1-win32-vs2008.zip')
    self.assertEqual(event_data.url, expected_url)

    expected_full_path = 'file:///D:/plaso-static-1.0.1-win32-vs2008.zip'
    self.assertEqual(event_data.full_path, expected_full_path)

    self.assertEqual(event_data.received_bytes, 15974599)
    self.assertEqual(event_data.total_bytes, 15974599)


if __name__ == '__main__':
  unittest.main()
