#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Defender DeviceFileEvents CSV parser."""

import unittest

from plaso.parsers import defender_device

from tests.parsers import test_lib


class DefenderDeviceFileEventsParserTest(test_lib.ParserTestCase):
  """Tests for the Defender DeviceFileEvents CSV parser."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    parser =  defender_device.DefenderDeviceFileEventsParser()
    storage_writer = self._ParseFile(
        ['advanced_hunting_test_002.csv'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 129)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'm365:defenderah:powershellcommand',
        'initiatingprocessid': '36112',
        'initiatingprocessfilename': 'a180powershellcollector.exe',
        'initiatingprocessparentid': '27456',
        'initiatingprocessparentfilename': 'A180AG.exe',
        'pscommand': 'Get-CimInstance'}
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 39)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'm365:defenderah:smartscreenurlwarning',
        'initiatingprocessid': '15440',
        'initiatingprocessfilename': 'msedge.exe',
        'initiatingprocessparentid': '11760',
        'initiatingprocessparentfilename': (
            '\\Device\\HarddiskVolume3\\Windows\\explorer.exe'),
        'remoteurl': 'https://tiktok.com/@pheromania.co',
        'additionalfields': (
            '{"Experience":"CustomBlockList","ApplicationName":"TikTok"}')}
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 58)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'm365:defenderah:useraccountaddedtolocalgroup',
        'initiatingprocessaccountdomain': 'workgroup',
        'initiatingprocessaccountname': 'test-hostname$',
        'groupdomainname': 'Builtin',
        'groupname': 'Administratorer'}
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 62)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'm365:defenderah:connectionrequest',
        'initiatingprocessfilename': 'Microsoft Word',
        'initiatingprocessid': '62399',
        'initiatingprocessparentid': '62399',
        'initiatingprocessparentfilename': 'xpcproxy',
        'remoteip': '52.98.149.162',
        'remoteport': '443',
        'remoteurl': '',
        'localip': '192.168.68.102',
        'localport': '56165',
        'protocol': 'Tcp'}
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 74)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'm365:defenderah:filerenamed',
        'filename': 'geo-20231221-195543-982-982725.zip',
        'sha1': 'fc98c75eec53f4ab6dc0be9559b1000276c22ffb',
        'previousfilename': 'geo-20231221-195543-982-982725.zip',
        'requestprotocol': 'Local',
        'requestaccountname': 'SYSTEM',
        'requestaccountdomain': 'NT AUTHORITY',
        'additionalfields': '{"FileType":"Zip"}'}
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 110)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
