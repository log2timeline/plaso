#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Diagnosed Applications Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import diagnosed_applications

from tests.parsers.winreg_plugins import test_lib


class WindowsRegistryDiagnosedApplicationsPluginTest(
    test_lib.RegistryPluginTestCase):
  """Tests for the Diagnosed Applications Windows Registry plugin."""

  def _CreateTestKey(self):
    """Creates Registry keys and values for testing.
    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString('2024-08-28 09:23:49.002031')
    self.registry_key = dfwinreg_fake.FakeWinRegistryKey(
      'chrome.exe',
      key_path_prefix='HKEY_LOCAL_MACHINE\\SOFTWARE',
      last_written_time=filetime.timestamp,
      relative_key_path='Microsoft\\RADAR\\HeapLeakDetection\\'
        'DiagnosedApplications\\chrome.exe'
    )

    registry_value = dfwinreg_fake.FakeWinRegistryValue(
      'LastDetectionTime',
      data=b'\xac\xbcu\xbe<u\xcc\x01',
      data_type=dfwinreg_definitions.REG_QWORD
    )
    self.registry_key.AddValue(registry_value)

  def testProcessValue(self):
    """Tests the Process function for Diagnosed Applications data."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE'])
    key_path = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\RADAR\\HeapLeakDetection\\DiagnosedApplications'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    plugin = diagnosed_applications.DiagnosedApplicationsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
      registry_key=registry_key,
      plugin=plugin
    )

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
      'process_name': 'TrustedInstaller.exe',
      'last_detection_time': '2011-09-17T13:21:44.0776364+00:00',
      'data_type': 'windows:registry:diagnosed_applications',
      'key_path': (
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\RADAR\\HeapLeakDetection'
          '\\DiagnosedApplications\\TrustedInstaller.exe'),
      'last_written_time': '2011-09-17T13:21:44.0776364+00:00'
    }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
