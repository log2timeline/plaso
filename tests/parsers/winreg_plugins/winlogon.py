#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Winlogon Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
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
    filetime.CopyFromString(time_string)
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        u'Winlogon', key_path=key_path,
        last_written_time=filetime.timestamp, offset=153)

    # Setup Winlogon values.
    value_data = u'1'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'AutoAdminLogon', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'AutoRestartShell', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = u'0 0 0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Background', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'10'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'CachedLogonsCount', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'no'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DebugServerCommand', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u''.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DefaultDomainName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'user'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DefaultUserName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x01'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DisableCAD', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ForceUnlockLogon', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = u''.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'LegalNoticeCaption', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u''.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'LegalNoticeText', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x05'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'PasswordExpiryWarning', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'PowerdownAfterShutdown', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'{A520A1A4-1780-4FF6-BD18-167343C5AF16}'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'PreCreateKnownFolders', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'1'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ReportBootOk', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'explorer.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Shell', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x2b'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ShutdownFlags', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'ShutdownWithoutLogon', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'C:\\Windows\\system32\\userinit.exe'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Userinit', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'SystemPropertiesPerformance.exe/pagefile'.encode(
        u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'VMApplet', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    value_data = u'0'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'WinStationsDisabled', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    # Setup registered event handlers.
    notify = dfwinreg_fake.FakeWinRegistryKey(u'Notify')
    registry_key.AddSubkey(notify)

    navlogon = dfwinreg_fake.FakeWinRegistryKey(
        u'NavLogon', last_written_time=filetime.timestamp)
    notify.AddSubkey(navlogon)

    value_data = u'NavLogon.dll'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DllName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    navlogon.AddValue(registry_value)

    value_data = u'NavLogoffEvent'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Logoff', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    navlogon.AddValue(registry_value)

    value_data = u'NavStartShellEvent'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'StartShell', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    navlogon.AddValue(registry_value)

    secret_malware = dfwinreg_fake.FakeWinRegistryKey(
        u'SecretMalware', last_written_time=filetime.timestamp)
    notify.AddSubkey(secret_malware)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Asynchronous', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    secret_malware.AddValue(registry_value)

    value_data = u'secret_malware.dll'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'DllName', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = b'\x00\x00\x00\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Impersonate', data=value_data,
        data_type=dfwinreg_definitions.REG_DWORD_BIG_ENDIAN)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventLock'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Lock', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventLogoff'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Logoff', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventLogon'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Logon', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventShutdown'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Shutdown', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventSmartCardLogonNotify'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'SmartCardLogonNotify', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventStartShell'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'StartShell', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventStartup'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Startup', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventStopScreenSaver'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'StopScreenSaver', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    value_data = u'secretEventUnlock'.encode(u'utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        u'Unlock', data=value_data,
        data_type=dfwinreg_definitions.REG_SZ)
    secret_malware.AddValue(registry_value)

    return registry_key

  def testProcess(self):
    """Tests the Process function on created key."""
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
    time_string = u'2013-01-30 10:47:57'
    registry_key = self._CreateTestKey(key_path, time_string)

    plugin = winlogon.WinlogonPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetSortedEvents())

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}\\Notify\\NavLogon] '
        u'Application: NavLogon '
        u'Command: NavLogon.dll '
        u'Handler: NavLogoffEvent '
        u'Trigger: Logoff').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(time_string)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'Application: VmApplet '
        u'Command: SystemPropertiesPerformance.exe/pagefile '
        u'Trigger: Logon').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
