#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome History database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import safari as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import safari

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class SafariHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Safari History database plugin ."""

  @shared_test_lib.skipUnlessHasTestFile(['History.db'])
  def testProcess(self):
    """Tests the process function on a Safari History.db database file."""

    plugin = safari.SafariHistoryPluginSqlite()
    cache = sqlite.SQLiteCache()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History.db'], plugin, cache=cache)

<<<<<<< HEAD
    # The History file contains 25 events
    self.assertEqual(storage_writer.number_of_events, 25)

    events = list(storage_writer.GetEvents())
    # Check the first page visited entry
=======
    # tThe History file contains 19 events.
    self.assertEqual(storage_writer.number_of_events, 25)

    events = list(storage_writer.GetEvents())
    # Check the first page visited entry.
>>>>>>> 942655f4c020b49c3970ee94646d418bd68e165b
    event = events[1]

    self.assertEqual(event.timestamp_desc,
                     definitions.TIME_DESCRIPTION_LAST_VISITED)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2017-11-09 21:24:28.829571')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_url = 'http://facebook.com/'
    self.assertEqual(event.url, expected_url)

    expected_title = ''
    self.assertEqual(event.title, expected_title)

    expected_message = (
<<<<<<< HEAD
        'URL: {0:s} [count: 2] Host: facebook http_non_get: False'
    ).format(expected_url)

=======
        'URL: http://facebook.com/ [count: 2] '
        'Host: facebook.com http_non_get: False')
>>>>>>> 942655f4c020b49c3970ee94646d418bd68e165b
    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '_main_':
  unittest.main()
