#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the M365 Defender DeviceImageLoadEvents table plugin."""

import unittest

from plaso.parsers.csv_plugins import dah_deviceimageloadevents

from tests.parsers.csv_plugins import test_lib

class DefenderAHDeviceImageLoadEventsTest(test_lib.CSVPluginTestCase):
  """Tests for the M365 Defender DeviceImageLoadEvents table plugin."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    plugin = dah_deviceimageloadevents.DefenderAHDeviceImageLoadEventsPlugin()
    storage_writer = self._ParseCSVFileWithPlugin(
        ['advanced_hunting_test.csv'],
        plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'm365:defenderah:imageloaded',
        'filename': 'dbghelp.dll',
        'sha1': '6c95e7ac84edede62d54328b8aa7f7a0284df1b7',
        'initiatingprocessid': '1532',
        'initiatingprocessparentid': '2244'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
