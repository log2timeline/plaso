#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the LS Quarantine database plugin."""

import unittest

from plaso.formatters import ls_quarantine as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import ls_quarantine

from tests.parsers.sqlite_plugins import test_lib


class LSQuarantinePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the LS Quarantine database plugin."""

  def testProcess(self):
    """Tests the Process function on a LS Quarantine database file."""
    plugin_object = ls_quarantine.LsQuarantinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'quarantine.db'], plugin_object)

    # The quarantine database contains 14 events.
    self.assertEqual(len(storage_writer.events), 14)

    # Examine a VLC event.
    event_object = storage_writer.events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 21:12:03')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.agent, u'Google Chrome')
    vlc_url = (
        u'http://download.cnet.com/VLC-Media-Player/3001-2139_4-10210434.html'
        u'?spi=40ab24d3c71594a5017d74be3b0c946c')
    self.assertEqual(event_object.url, vlc_url)

    self.assertTrue(u'vlc-2.0.7-intel64.dmg' in event_object.data)

    # Examine a MacKeeper event.
    event_object = storage_writer.events[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 19:28:58')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Examine a SpeedTest event.
    event_object = storage_writer.events[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 19:30:16')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    speedtest_message = (
        u'[Google Chrome] Downloaded: http://mackeeperapp.zeobit.com/aff/'
        u'speedtest.net.6/download.php?affid=460245286&trt=5&utm_campaign='
        u'3ES&tid_ext=P107fSKcSfqpMbcP3sI4fhKmeMchEB3dkAGpX4YIsvM;US;L;1 '
        u'<http://download.mackeeper.zeobit.com/package.php?'
        u'key=460245286&trt=5&landpr=Speedtest>')
    speedtest_short = (
        u'http://mackeeperapp.zeobit.com/aff/speedtest.net.6/download.php?'
        u'affid=4602452...')

    self._TestGetMessageStrings(
        event_object, speedtest_message, speedtest_short)


if __name__ == '__main__':
  unittest.main()
