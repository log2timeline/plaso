#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacKeeper Cache database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import mackeeper_cache

from tests.parsers.sqlite_plugins import test_lib


class MacKeeperCachePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacKeeper Cache database plugin."""

  def testProcess(self):
    """Tests the Process function on a MacKeeper Cache database file."""
    plugin = mackeeper_cache.MacKeeperCachePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mackeeper_cache.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 198)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2013-07-12T19:30:31+00:00',
        'data_type': 'mackeeper:cache',
        'description': 'Chat Outgoing Message',
        'record_id': 16059074,
        'room': '12828340738351e0593f987450z40787',
        'text': (
            'I have received your system scan report and I will start '
            'analyzing it right now.'),
        'url': (
            'http://support.kromtech.net/chat/listen/12828340738351e0593f98745'
            '0z40787/?client-id=51e0593fa1a24468673655&callback=jQuery18301357'
            '1173651143909_1373657420912&_=1373657423647')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 41)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
