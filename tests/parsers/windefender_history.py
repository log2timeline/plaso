#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Defender History parser."""

import unittest

from plaso.parsers import windefender_history

from tests.parsers import test_lib


class WinDefenderHistoryUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows Defender History parser."""

  def testWebFileDetection(self):
    """Tests parsing a webfile Detection History file."""
    parser = windefender_history.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
        'FC380697-A68D-4C94-B67F-9B6449039463'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'av:defender:detection_history',
        'filename': 'C:\\Users\\testuser\\Downloads\\PotentiallyUnwanted.exe',
        'host_and_user': 'FRYPTOP\\testuser',
        'process': 'C:\\Windows\\explorer.exe',
        'recorded_time': '2022-07-22T05:32:27.8302783+00:00',
        'sha256': (
            'd6f6c6b9fde37694e12b12009ad11ab9ec8dd0f193e7319c523933bdad8a50ad'),
        'threat_name': 'PUA:Win32/EICAR_Test_File',
        'web_filenames': [(
            'C:\\Users\\testuser\\Downloads\\PotentiallyUnwanted.exe|'
            'http://amtso.eicar.org/PotentiallyUnwanted.exe|'
            'pid:19588,ProcessStart:133029415464710822')]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testContainerDetection(self):
    """Tests parsing a containerfile Detection History file."""
    parser = windefender_history.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
        '6AFE33A0-19BA-4FFF-892F-B700539D7D63'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'container_filenames': [
            'C:\\Users\\testuser\\Downloads\\eicar_com.zip'],
        'data_type': 'av:defender:detection_history',
        'filename': 'C:\\Users\\testuser\\Downloads\\eicar_com.zip->eicar.com',
        'host_and_user': 'FRYPTOP\\testuser',
        'process': 'Unknown',
        'recorded_time': '2022-07-22T05:36:18.9094421+00:00',
        'sha256': (
            '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f'),
        'threat_name': 'Virus:DOS/EICAR_Test_File',
        'web_filenames': [(
            'C:\\Users\\testuser\\Downloads\\eicar_com.zip|'
            'https://secure.eicar.org/eicar_com.zip|'
            'pid:20580,ProcessStart:133029417782902463')]}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
