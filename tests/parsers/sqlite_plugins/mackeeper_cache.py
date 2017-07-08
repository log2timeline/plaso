#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MacKeeper Cache database plugin."""

import unittest

from plaso.formatters import mackeeper_cache  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import mackeeper_cache

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class MacKeeperCachePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacKeeper Cache database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'mackeeper_cache.db'])
  def testProcess(self):
    """Tests the Process function on a MacKeeper Cache database file."""
    plugin = mackeeper_cache.MacKeeperCachePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'mackeeper_cache.db'], plugin)

    # The cache file contains 198 entries.
    self.assertEqual(storage_writer.number_of_events, 198)

    events = list(storage_writer.GetEvents())

    event = events[41]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 19:30:31')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Chat Outgoing Message : I have received your system scan report and '
        u'I will start analyzing it right now. [ URL: http://support.kromtech.'
        u'net/chat/listen/12828340738351e0593f987450z40787/?client-id=51e0593f'
        u'a1a24468673655&callback=jQuery183013571173651143909_1373657420912&_='
        u'1373657423647 Event ID: 16059074 Room: '
        u'12828340738351e0593f987450z40787 ]')

    expected_short_message = (
        u'I have received your system scan report and I will start analyzing '
        u'it right now.')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
