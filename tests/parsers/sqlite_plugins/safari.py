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

<<<<<<< HEAD

=======
>>>>>>> 7cb02afa34ae40ecec2f0332b82cc0dd161ea699
class SafariHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Safari History database plugin ."""

  @shared_test_lib.skipUnlessHasTestFile(['History.db'])
  def testProcess(self):
    """Tests the process function on a Safari History.db database file."""

    plugin = safari.SafariHistoryPluginSqlite()
    cache = sqlite.SQLiteCache()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['History.db'], plugin, cache=cache)

    # the History file contains 19 events
    self.assertEqual(storage_writer.number_of_events, 25)

    events = list(storage_writer.GetEvents())
<<<<<<< HEAD
    #check the first page visited entry
    event = events[1]

    self.assertEqual(event.timestamp_desc,
                     definitions.TIME_DESCRIPTION_LAST_VISITED)
=======
  	#check the first page visited entry
    event = events[1]

    self.assertEqual(event.timestamp_desc,
        definitions.TIME_DESCRIPTION_LAST_VISITED)
>>>>>>> 7cb02afa34ae40ecec2f0332b82cc0dd161ea699

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2017-11-09 21:24:28.829571')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_url = 'http://facebook.com/'
    self.assertEqual(event.url, expected_url)

    expected_title = ''
    self.assertEqual(event.title, expected_title)

    expected_message = (
<<<<<<< HEAD
        'URL: {0:s} [count: 2] Host: facebook.com http_non_get: False'
    ).format(expected_url)
=======
        'URL: {0:s} [count: 2] Host: facebook.com http_non_get: False').format(
            expected_url)
>>>>>>> 7cb02afa34ae40ecec2f0332b82cc0dd161ea699

    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '_main_':
  unittest.main()
