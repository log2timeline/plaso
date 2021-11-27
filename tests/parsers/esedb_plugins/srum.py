#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the System Resource Usage Monitor (SRUM) ESE database file."""

import collections
import unittest

from plaso.lib import definitions
from plaso.parsers.esedb_plugins import srum

from tests.parsers.esedb_plugins import test_lib


class SystemResourceUsageMonitorESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the System Resource Usage Monitor (SRUM) ESE database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = srum.SystemResourceUsageMonitorESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(['SRUDB.dat'], plugin)

    # TODO: confirm this is working as intended. Also see: #2134
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 18543)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    data_types = collections.Counter()
    for event in events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      data_types[event_data.data_type] += 1

    self.assertEqual(len(data_types.keys()), 3)
    self.assertEqual(data_types['windows:srum:application_usage'], 16183)
    self.assertEqual(data_types['windows:srum:network_connectivity'], 520)
    self.assertEqual(data_types['windows:srum:network_usage'], 1840)

    # Test event with data type windows:srum:application_usage
    expected_event_values = {
        'application': 'Memory Compression',
        'data_type': 'windows:srum:application_usage',
        'date_time': '2017-11-05 11:32:00.000000',
        'identifier': 22167,
        'timestamp_desc': definitions.TIME_DESCRIPTION_SAMPLE}

    self.CheckEventValues(storage_writer, events[92], expected_event_values)

    # Test event with data type windows:srum:network_connectivity
    expected_event_values = {
        'application': 1,
        'data_type': 'windows:srum:network_connectivity',
        'date_time': '2017-11-05 10:30:48.1679714',
        'identifier': 501,
        'timestamp_desc': definitions.TIME_DESCRIPTION_FIRST_CONNECTED}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Test event with data type windows:srum:network_usage
    expected_event_values = {
        'application': 'DiagTrack',
        'bytes_sent': 2076,
        'data_type': 'windows:srum:network_usage',
        'date_time': '2017-11-05 11:32:00.000000',
        'identifier': 3495,
        'interface_luid': 1689399632855040,
        'timestamp_desc': definitions.TIME_DESCRIPTION_SAMPLE,
        'user_identifier': 'S-1-5-18'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)


if __name__ == '__main__':
  unittest.main()
