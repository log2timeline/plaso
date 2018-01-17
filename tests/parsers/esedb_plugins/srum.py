#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the System Resource Usage Monitor (SRUM) ESE database file."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import srum as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.esedb_plugins import srum

from tests import test_lib as shared_test_lib
from tests.parsers.esedb_plugins import test_lib


class SystemResourceUsageMonitorESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the System Resource Usage Monitor (SRUM) ESE database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SRUDB.dat'])
  def testProcess(self):
    """Tests the Process function."""
    plugin = srum.SystemResourceUsageMonitorESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(['SRUDB.dat'], plugin)

    self.assertEqual(storage_writer.number_of_events, 18543)

    events = list(storage_writer.GetSortedEvents())

    event = events[14]

    self.assertEqual(event.identifier, 3495)

    expected_timestamp = timelib.Timestamp.CopyFromString('2017-11-05 11:32:00')

    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_SAMPLE)

    expected_message = (
        'Application: DiagTrack '
        'Bytes sent: 2076 '
        'Interface LUID: 1689399632855040 '
        'User identifer: S-1-5-18')

    expected_short_message = 'DiagTrack'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
