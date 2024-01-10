#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the M365 Defender DeviceProcessEvents table plugin."""

import unittest

from plaso.parsers.csv_plugins import dah_deviceprocessevents

from tests.parsers.csv_plugins import test_lib

class DefenderAHDeviceProcessEventsTest(test_lib.CSVPluginTestCase):
  """Tests for the M365 Defender DeviceProcessEvents table plugin."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the DeviceProcessEvents function."""
    plugin = dah_deviceprocessevents.DefenderAHDeviceProcessEventsPlugin()
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
        'data_type': 'm365:defenderah:processcreated',
        'filename': 'CompatTelRunner.exe',
        'sha1': '86214f7f3a8ac4b824c23ef54f65d60ec5bc8618',
        'processid': '11080',
        'accountdomain': 'nt authority',
        'accountname': 'system'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
