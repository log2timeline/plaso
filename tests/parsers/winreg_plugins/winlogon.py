#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Winlogon Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import winlogon

from tests.parsers.winreg_plugins import test_lib


class WinlogonPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Winlogon Windows Registry plugin."""

  def _CreateTestKey(self, key_path, time_string):
    """Creates Registry keys and values for testing.

    Args:
      key_path (str): Windows Registry key path.
      time_string (str): key last written date and time.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    filetime = dfdatetime_filetime.Filetime()
    filetime.CopyFromDateTimeString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Winlogon', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    # Setup Winlogon values.
    value_data = '1'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'AutoAdminLogon', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'AutoRestartShell', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = '0 0 0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Background', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = '10'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'CachedLogonsCount', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = 'no'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DebugServerCommand', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = ''.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DefaultDomainName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = 'user'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DefaultUserName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DisableCAD', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ForceUnlockLogon', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = ''.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'LegalNoticeCaption', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = ''.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'LegalNoticeText', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x05'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'PasswordExpiryWarning', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'PowerdownAfterShutdown', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = '{A520A1A4-1780-4FF6-BD18-167343C5AF16}'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'PreCreateKnownFolders', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = '1'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ReportBootOk', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = 'explorer.exe'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Shell', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x2b'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ShutdownFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'ShutdownWithoutLogon', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = 'C:\\Windows\\system32\\userinit.exe'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Userinit', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = 'SystemPropertiesPerformance.exe/pagefile'.encode(
        'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'VMApplet', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = '0'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'WinStationsDisabled', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    # Setup registered event handlers.
    notify = dfwinreg_fake.FakeWinRegistryKey('Notify')
    registry_key.AddSubkey(notify)

    navlogon = dfwinreg_fake.FakeWinRegistryKey(
        'NavLogon', last_written_time=filetime.timestamp)
    notify.AddSubkey(navlogon)

    value_data = 'NavLogon.dll'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DllName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    navlogon.AddValue(registry_value)

    value_data = 'NavLogoffEvent'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Logoff', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    navlogon.AddValue(registry_value)

    value_data = 'NavStartShellEvent'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'StartShell', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    navlogon.AddValue(registry_value)

    secret_malware = dfwinreg_fake.FakeWinRegistryKey(
        'SecretMalware', last_written_time=filetime.timestamp)
    notify.AddSubkey(secret_malware)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Asynchronous', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    secret_malware.AddValue(registry_value)

    value_data = 'secret_malware.dll'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'DllName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Impersonate', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventLock'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Lock', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventLogoff'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Logoff', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventLogon'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Logon', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventShutdown'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Shutdown', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventSmartCardLogonNotify'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'SmartCardLogonNotify', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventStartShell'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'StartShell', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventStartup'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Startup', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventStopScreenSaver'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'StopScreenSaver', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = 'secretEventUnlock'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'Unlock', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = winlogon.WinlogonPlugin()

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion\\'
        'Winlogon')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function on created key."""
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
    time_string = '2013-01-30 10:47:57'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = winlogon.WinlogonPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetSortedEvents())

    test_event_data1 = None
    test_event_data2 = None
    for event in events:
      self.CheckTimestamp(event.timestamp, '2013-01-30 10:47:57.000000')

      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(event_data.data_type, 'windows:registry:winlogon')

      if event_data.application == 'VmApplet':
        test_event_data1 = event_data
      elif (event_data.application == 'NavLogon' and
            event_data.trigger == 'Logoff'):
        test_event_data2 = event_data

    expected_message = (
        '[{0:s}] '
        'Application: VmApplet '
        'Command: SystemPropertiesPerformance.exe/pagefile '
        'Trigger: Logon').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        test_event_data1, expected_message, expected_short_message)

    expected_message = (
        '[{0:s}\\Notify\\NavLogon] '
        'Application: NavLogon '
        'Command: NavLogon.dll '
        'Handler: NavLogoffEvent '
        'Trigger: Logoff').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        test_event_data2, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
