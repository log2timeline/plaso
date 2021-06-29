#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mozilla Firefox downloads database plugin."""

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

    self.assertEqual(storage_writer.number_of_events, 2)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the first page visited event.
    expected_event_values = {
        'data_type': 'firefox:downloads:download',
        'date_time': '2013-07-18 18:59:59.312000',
        'full_path': 'file:///D:/plaso-static-1.0.1-win32-vs2008.zip',
        'received_bytes': 15974599,
        'timestamp_desc': definitions.TIME_DESCRIPTION_START,
        'total_bytes': 15974599,
        'url': (
            'https://plaso.googlecode.com/files/'
            'plaso-static-1.0.1-win32-vs2008.zip')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
