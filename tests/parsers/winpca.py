#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Program Compatibility Assistant (PCA) log parsers."""

import unittest

from plaso.parsers import winpca
from tests.parsers import test_lib


class WindowsPCADB0ParserTest(test_lib.ParserTestCase):
  """Tests for the Program Compatibility Assistant DB0 log files parser."""

  def testParse(self):
    """Tests the Parse function."""
    plugin = winpca.WindowsPCADB0Parser()
    storage_writer = self._ParseFile(['PcaGeneralDb0.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'description': 'microsoft teams updater',
        'executable': (
            '%programfiles%\\windowsapps\\microsoftteams_22287'
            '.702.1670.9453_x64__8wekyb3d8bbwe\\msteamsupdate.exe'),
        'exit_code': 'Abnormal process exit with code 0x4c7',
        'last_execution_time': '2022-11-14T23:37:11.789+00:00',
        'program_identifier': '0006132687b1e64961e910ee21d4352afe0800000904',
        'run_status': '2',
        'vendor': 'microsoft corporation',
        'version': '22287.702.1670.9453'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class WindowsPCADicParserTest(test_lib.ParserTestCase):
  """Tests for the Program Compatibility Assistant DIC log files parser."""

  def testParse(self):
    """Tests the Parse function."""
    plugin = winpca.WindowsPCADicParser()
    storage_writer = self._ParseFile(['PcaAppLaunchDic.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'executable': (
            'C:\\Program Files\\WindowsApps\\MicrosoftTeams_'
            '22287.702.1670.9453_x64__8wekyb3d8bbwe\\msteams.exe'),
        'last_execution_time': '2022-11-15T00:02:08.476+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
