#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the UserAssist Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import userassist

from tests.parsers.winreg_plugins import test_lib


class UserAssistPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the UserAssist Windows Registry plugin."""

  _TEST_GUIDS = [
      '{0D6D4F41-2994-4BA0-8FEF-620E43CD2812}',
      '{5E6AB780-7743-11CF-A12B-00AA004AE837}',
      '{75048700-EF1F-11D0-9888-006097DEACF9}',
      '{9E04CAB2-CC14-11DF-BB8C-A2F1DED72085}',
      '{A3D53349-6E61-4557-8FC7-0028EDCEEBF6}',
      '{B267E3AD-A825-4A09-82B9-EEC22AA3B847}',
      '{BCB48336-4DDD-48FF-BB0B-D3190DACB3E2}',
      '{CAA59E3C-4792-41A5-9909-6A6A8D32490E}',
      '{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}',
      '{F2A1CB5A-E3CC-4A2E-AF9D-505A7009D442}',
      '{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}',
      '{FA99DFC7-6AC2-453A-A5E2-5E2AFF4507BD}']

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = userassist.UserAssistPlugin()

    for guid in self._TEST_GUIDS:
      key_path = (
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\UserAssist\\{0:s}').format(guid)
      self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcessOnWinXP(self):
    """Tests the Process function on a Windows XP Registry file."""
    test_file_entry = self._GetTestFileEntry(['NTUSER.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\UserAssist\\{75048700-EF1F-11D0-9888-006097DEACF9}')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = userassist.UserAssistPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:registry:userassist',
        'key_path': '{0:s}\\Count'.format(key_path),
        'last_execution_time': '2009-08-04T15:11:22.8110676+00:00',
        'number_of_executions': 14,
        'value_name': 'UEME_RUNPIDL:%csidl2%\\MSN.lnk'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessOnWin7(self):
    """Tests the Process function on a Windows 7 Registry file."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\UserAssist\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = userassist.UserAssistPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 61)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application_focus_count': 21,
        'application_focus_duration': 420000,
        'data_type': 'windows:registry:userassist',
        'key_path': '{0:s}\\Count'.format(key_path),
        'last_execution_time': '2010-11-10T07:49:37.0780676+00:00',
        'number_of_executions': 14,
        'value_name': 'Microsoft.Windows.GettingStarted'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
