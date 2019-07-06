#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacKeeper Cache database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mackeeper_cache as _  # pylint: disable=unused-import
from plaso.parsers.sqlite_plugins import mackeeper_cache

from tests.parsers.sqlite_plugins import test_lib


class MacKeeperCachePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacKeeper Cache database plugin."""

  def testProcess(self):
    """Tests the Process function on a MacKeeper Cache database file."""
    plugin = mackeeper_cache.MacKeeperCachePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mackeeper_cache.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 198)

    events = list(storage_writer.GetEvents())

    event = events[41]

    self.CheckTimestamp(event.timestamp, '2013-07-12 19:30:31.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Chat Outgoing Message : I have received your system scan report and '
        'I will start analyzing it right now. [ URL: http://support.kromtech.'
        'net/chat/listen/12828340738351e0593f987450z40787/?client-id=51e0593f'
        'a1a24468673655&callback=jQuery183013571173651143909_1373657420912&_='
        '1373657423647 Event ID: 16059074 Room: '
        '12828340738351e0593f987450z40787 ]')

    expected_short_message = (
        'I have received your system scan report and I will start analyzing '
        'it right now.')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
