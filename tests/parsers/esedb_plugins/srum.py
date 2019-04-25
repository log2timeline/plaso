#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the System Resource Usage Monitor (SRUM) ESE database file."""

from __future__ import unicode_literals

import collections
import unittest

from plaso.formatters import srum as _  # pylint: disable=unused-import
from plaso.lib import definitions
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

    # TODO: confirm this is working as intended. Also see: #2134
    self.assertEqual(storage_writer.number_of_warnings, 2)
    self.assertEqual(storage_writer.number_of_events, 18543)

    events = list(storage_writer.GetSortedEvents())

    data_types = collections.Counter()
    for event in events:
      data_types[event.data_type] += 1

    self.assertEqual(len(data_types.keys()), 3)
    self.assertEqual(data_types['windows:srum:application_usage'], 16183)
    self.assertEqual(data_types['windows:srum:network_connectivity'], 520)
    self.assertEqual(data_types['windows:srum:network_usage'], 1840)

    # Test event with data type windows:srum:application_usage
    event = events[21]

    self.CheckTimestamp(event.timestamp, '2017-11-05 11:32:00.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_SAMPLE)

    self.assertEqual(event.data_type, 'windows:srum:application_usage')
    self.assertEqual(event.identifier, 22167)

    expected_message = (
        'Application: Memory Compression')

    expected_short_message = 'Memory Compression'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test event with data type windows:srum:network_connectivity
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2017-11-05 10:30:48.167971')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_FIRST_CONNECTED)

    self.assertEqual(event.data_type, 'windows:srum:network_connectivity')
    self.assertEqual(event.identifier, 501)

    expected_message = (
        'Application: 1')

    expected_short_message = '1'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test event with data type windows:srum:network_usage
    event = events[14]

    self.CheckTimestamp(event.timestamp, '2017-11-05 11:32:00.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_SAMPLE)

    self.assertEqual(event.data_type, 'windows:srum:network_usage')
    self.assertEqual(event.identifier, 3495)

    expected_message = (
        'Application: DiagTrack '
        'Bytes sent: 2076 '
        'Interface LUID: 1689399632855040 '
        'User identifier: S-1-5-18')

    expected_short_message = 'DiagTrack'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
