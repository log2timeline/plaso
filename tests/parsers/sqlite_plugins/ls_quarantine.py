#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the LS Quarantine database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.parsers.sqlite_plugins import ls_quarantine

from tests.parsers.sqlite_plugins import test_lib


class LSQuarantinePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the LS Quarantine database plugin."""

  def testProcess(self):
    """Tests the Process function on a LS Quarantine database file."""
    plugin = ls_quarantine.LsQuarantinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['quarantine.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetEvents())

    # Examine a VLC event.
    expected_event_values = {
        'agent': 'Google Chrome',
        'timestamp': '2013-07-08 21:12:03.000000',
        'url': (
            'http://download.cnet.com/VLC-Media-Player/'
            '3001-2139_4-10210434.html?spi=40ab24d3c71594a5017d74be3b0c946c')}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Examine a MacKeeper event.
    expected_event_values = {
        'timestamp': '2013-07-12 19:28:58.000000'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    # Examine a SpeedTest event.
    expected_event_values = {
        'timestamp': '2013-07-12 19:30:16.000000'}

    self.CheckEventValues(storage_writer, events[10], expected_event_values)

    expected_message = (
        '[Google Chrome] Downloaded: http://mackeeperapp.zeobit.com/aff/'
        'speedtest.net.6/download.php?affid=460245286&trt=5&utm_campaign='
        '3ES&tid_ext=P107fSKcSfqpMbcP3sI4fhKmeMchEB3dkAGpX4YIsvM;US;L;1 '
        '<http://download.mackeeper.zeobit.com/package.php?'
        'key=460245286&trt=5&landpr=Speedtest>')
    expected_short_message = (
        'http://mackeeperapp.zeobit.com/aff/speedtest.net.6/download.php?'
        'affid=4602452...')

    event_data = self._GetEventDataOfEvent(storage_writer, events[10])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
