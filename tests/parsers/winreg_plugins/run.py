#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Run Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import run

from tests.parsers.winreg_plugins import test_lib


class AutoRunsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the auto rus Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = run.AutoRunsPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Run')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'RunOnce')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Run')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'RunOnce')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'RunOnce\\Setup')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'RunServices')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'RunServicesOnce')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcessNtuserRun(self):
    """Tests the Process function on a Run key."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-RunTests.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Run')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

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
        'data_type': 'windows:registry:run',
        'entries': [
            'Sidebar: %ProgramFiles%\\Windows Sidebar\\Sidebar.exe /autoRun'],
        'key_path': key_path,
        'last_written_time': '2012-04-05T17:03:53.9920616+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessNtuserRunOnce(self):
    """Tests the Process function on a Run key."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-RunTests.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'RunOnce')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

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
        'data_type': 'windows:registry:run',
        'entries': [
            'mctadmin: C:\\Windows\\System32\\mctadmin.exe'],
        'key_path': key_path,
        'last_written_time': '2012-04-05T17:03:53.9920616+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessSoftwareRun(self):
    """Tests the Process function on a Run key."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE-RunTests'])
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Run')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

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
        'data_type': 'windows:registry:run',
        'entries': [
            ('McAfee Host Intrusion Prevention Tray: "C:\\Program Files\\'
             'McAfee\\Host Intrusion Prevention\\FireTray.exe"'),
            ('VMware Tools: "C:\\Program Files\\VMware\\VMware Tools\\'
             'VMwareTray.exe"'),
            ('VMware User Process: "C:\\Program Files\\VMware\\VMware Tools\\'
             'VMwareUser.exe"')],
        'key_path': key_path,
        'last_written_time': '2011-09-16T20:57:09.0675758+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessSoftwareRunOnce(self):
    """Tests the Process function on a RunOnce key."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE-RunTests'])
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'RunOnce')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

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
        'data_type': 'windows:registry:run',
        'entries': [
            '*WerKernelReporting: %SYSTEMROOT%\\SYSTEM32\\WerFault.exe -k -rq'],
        'key_path': key_path,
        'last_written_time': '2012-04-06T14:07:27.7500000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
