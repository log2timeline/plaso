#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the M365 Defender DeviceNetworkEvents table plugin."""

import unittest

from plaso.parsers.csv_plugins import dah_devicenetworkevents

from tests.parsers.csv_plugins import test_lib

class DefenderAHDeviceNetworkEventsTest(test_lib.CSVPluginTestCase):
  """Tests for the M365 Defender DeviceNetworkEvents table plugin."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    plugin = dah_devicenetworkevents.DefenderAHDeviceNetworkEventsPlugin()
    storage_writer = self._ParseCSVFileWithPlugin(
        ['advanced_hunting_test.csv'],
        plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 32)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'm365:defenderah:ftpconnectioninspected',
        'remoteip': '81.93.165.188',
        'remoteport': '21',
        'localip': '139.107.194.50',
        'localport': '60280',
        'protocol': 'Tcp',
        'direction': '->'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 14)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
