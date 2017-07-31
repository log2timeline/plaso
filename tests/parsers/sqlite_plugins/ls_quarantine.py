#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the LS Quarantine database plugin."""

import unittest

from plaso.formatters import ls_quarantine  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import ls_quarantine

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class LSQuarantinePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the LS Quarantine database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'quarantine.db'])
  def testProcess(self):
    """Tests the Process function on a LS Quarantine database file."""
    plugin = ls_quarantine.LsQuarantinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'quarantine.db'], plugin)

    # The quarantine database contains 14 events.
    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetEvents())

    # Examine a VLC event.
    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 21:12:03')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.agent, u'Google Chrome')
    expected_url = (
        u'http://download.cnet.com/VLC-Media-Player/3001-2139_4-10210434.html'
        u'?spi=40ab24d3c71594a5017d74be3b0c946c')
    self.assertEqual(event.url, expected_url)

    self.assertTrue(u'vlc-2.0.7-intel64.dmg' in event.data)

    # Examine a MacKeeper event.
    event = events[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 19:28:58')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Examine a SpeedTest event.
    event = events[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 19:30:16')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[Google Chrome] Downloaded: http://mackeeperapp.zeobit.com/aff/'
        u'speedtest.net.6/download.php?affid=460245286&trt=5&utm_campaign='
        u'3ES&tid_ext=P107fSKcSfqpMbcP3sI4fhKmeMchEB3dkAGpX4YIsvM;US;L;1 '
        u'<http://download.mackeeper.zeobit.com/package.php?'
        u'key=460245286&trt=5&landpr=Speedtest>')
    expected_short_message = (
        u'http://mackeeperapp.zeobit.com/aff/speedtest.net.6/download.php?'
        u'affid=4602452...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
