#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Defender History parser."""

import unittest

from plaso.parsers import windefenderhistory

from tests.parsers import test_lib


class WinDefenderHistoryUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows Defender History parser."""

  def testWebFileDetection(self):
    """Tests parsing a webfile Detection History file."""
    parser = windefenderhistory.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
        'FC380697-A68D-4C94-B67F-9B6449039463'], parser)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(
          'C:\\Users\\testuser\\Downloads\\PotentiallyUnwanted.exe',
          event_data.filename)
      self.assertEqual(
          'd6f6c6b9fde37694e12b12009ad11ab9ec8dd0f193e7319c523933bdad8a50ad',
          event_data.sha256)
      self.assertEqual('PUA:Win32/EICAR_Test_File', event_data.threat_name)
      self.assertEqual(
          'C:\\Users\\testuser\\Downloads\\PotentiallyUnwanted.exe|'
          'http://amtso.eicar.org/PotentiallyUnwanted.exe|'
          'pid:19588,ProcessStart:133029415464710822',
          event_data.web_filename)
      self.assertEqual('FRYPTOP\\testuser',
          event_data.host_and_user)
      self.assertEqual('C:\\Windows\\explorer.exe', event_data.process)

  def testContainerDetection(self):
    """Tests parsing a containerfile Detection History file."""
    parser = windefenderhistory.WinDefenderHistoryParser()
    storage_writer = self._ParseFile([
      '6AFE33A0-19BA-4FFF-892F-B700539D7D63'], parser)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(
          'C:\\Users\\testuser\\Downloads\\eicar_com.zip->eicar.com',
          event_data.filename)
      self.assertEqual(
        'C:\\Users\\testuser\\Downloads\\eicar_com.zip',
        event_data.container_filename)
      self.assertEqual(
          '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f',
          event_data.sha256)
      self.assertEqual('Virus:DOS/EICAR_Test_File', event_data.threat_name)
      self.assertEqual('FRYPTOP\\testuser',
          event_data.host_and_user)
      self.assertEqual('Unknown', event_data.process)
      self.assertEqual('2022-07-22 05:36:18',
          event.date_time.CopyToDateTimeString())


if __name__ == '__main__':
  unittest.main()
