#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Win PCA log text parser plugin."""

from plaso.parsers.text_plugins import winpca
from tests.parsers.text_plugins import test_lib


class WinPCALogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Apache access log text parser plugin."""

  def testLaunchDicParser(self):
    """Tests the LaunchDic file parser."""
    plugin = winpca.WinPCALogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['PcaAppLaunchDic.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 55)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': ('C:\\ProgramData\\Sophos\\AutoUpdate\\Cache\\'
            'sophos_autoupdate1.dir\\su-setup32.exe'),
        'last_written_time': '2022-12-17T13:27:53.096+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testDb0Parser(self):
    """Tests the db0 file parser."""
    plugin = winpca.WinPCALogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['PcaGeneralDb0.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 51)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'run_status': '2',
        'body': ('%programfiles%\\freefilesync\\freefilesync.exe'),
        'description': 'freefilesync',
        'vendor': 'freefilesync.org',
        'version': '11.20',
        'program_id': '000617915288ba535b4198ae58be4d9e2a4200000904',
        'exit_code': 'Abnormal process exit with code 0x2',
        'last_written_time': '2022-05-12T19:48:09.548+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)