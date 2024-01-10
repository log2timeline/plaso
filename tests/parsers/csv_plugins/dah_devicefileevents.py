#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the M365 Defender DeviceFileEvents table plugin."""

import unittest

from plaso.parsers.csv_plugins import dah_devicefileevents

from tests.parsers.csv_plugins import test_lib

class DefenderAHDeviceFileEventsTest(test_lib.CSVPluginTestCase):
  """Tests for the M365 Defender DeviceFileEvents table plugin."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    plugin = dah_devicefileevents.DefenderAHDeviceFileEventsPlugin()
    storage_writer = self._ParseCSVFileWithPlugin(
        ['advanced_hunting_test.csv'],
        plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'm365:defenderah:filerenamed',
        'filename': 'geo-20231221-195543-982-982725.zip',
        'sha1': 'fc98c75eec53f4ab6dc0be9559b1000276c22ffb',
        'previousfilename': 'geo-20231221-195543-982-982725.zip',
        'requestprotocol': 'Local',
        'requestaccountname': 'SYSTEM',
        'requestaccountdomain': 'NT AUTHORITY',
        'additionalfields': '{"FileType":"Zip"}'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
