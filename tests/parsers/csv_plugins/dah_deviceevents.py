#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the M365 Defender DeviceEvents table plugin."""

import unittest

from plaso.parsers.csv_plugins import dah_deviceevents

from tests.parsers.csv_plugins import test_lib

class DefenderAHDeviceEventsTest(test_lib.CSVPluginTestCase):
  """Tests for the M365 Defender DeviceEvents table plugin."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    plugin = dah_deviceevents.DefenderAHDeviceEventsPlugin()
    storage_writer = self._ParseCSVFileWithPlugin(
        ['advanced_hunting_test.csv'],
        plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 63)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'm365:defenderah:dnsqueryresponse',
        'dnsquery': 'tr.snapchat.com',
        'initiatingprocessaccountdomain': 'nt authority',
        'initiatingprocessaccountname': 'network service',
        'initiatingprocesssha1': '3f64c98f22da277a07cab248c44c56eedb796a81',
        'initiatingprocessfilename': 'svchost.exe',
        'initiatingprocessid': '3344',
        'initiatingprocesscommandline': 'svchost.exe -k NetworkService -p',
        'initiatingprocesscreationtime': '2023-12-20T08:46:08.6073895Z',
        'initiatingprocessparentid': '1196',
        'initiatingprocessparentfilename': 'services.exe',
        'initiatingprocessparentcreationtime': '2023-12-20T08:46:05.273693Z'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 21)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
