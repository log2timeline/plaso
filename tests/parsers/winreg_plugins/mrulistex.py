#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MRUListEx Windows Registry plugin."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import mrulistex

from tests.parsers.winreg_plugins import test_lib


class TestMRUListExStringWindowsRegistryPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the string MRUListEx plugin."""

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
        'MRUlist', key_path=key_path,
        last_written_time=filetime.timestamp, offset=1456)

    # The order is: 201
    value_data = (
        b'\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'MRUListEx', data=value_data,
        data_type=dfwinreg_definitions.REG_BINARY, offset=123)
    registry_key.AddValue(registry_value)

    value_data = 'Some random text here'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        '0', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1892)
    registry_key.AddValue(registry_value)

    value_data = 'c:\\evil.exe\x00'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        '1', data=value_data, data_type=dfwinreg_definitions.REG_BINARY,
        offset=612)
    registry_key.AddValue(registry_value)

    value_data = 'C:\\looks_legit.exe'.encode('utf_16_le')
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        '2', data=value_data, data_type=dfwinreg_definitions.REG_SZ,
        offset=1001)
    registry_key.AddValue(registry_value)

    return registry_key

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = mrulistex.MRUListExStringWindowsRegistryPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Some Windows\\'
        'InterestingApp\\MRUlist')
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'MRUlist', key_path=key_path)

    result = self._CheckFiltersOnKeyPath(plugin, registry_key)
    self.assertFalse(result)

    registry_value = dfwinreg_fake.FakeWinRegistryValue('MRUListEx')
    registry_key.AddValue(registry_value)

    registry_value = dfwinreg_fake.FakeWinRegistryValue('0')
    registry_key.AddValue(registry_value)

    result = self._CheckFiltersOnKeyPath(plugin, registry_key)
    self.assertTrue(result)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU')
    self._AssertNotFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\ComDlg32\\OpenSavePidlMRU')
    self._AssertNotFiltersOnKeyPath(plugin, key_path)

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Some Windows\\'
        'InterestingApp\\MRUlist')
    registry_key = self._CreateTestKey(key_path, '2012-08-28 09:23:49.002031')

    plugin = mrulistex.MRUListExStringWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # MRUListEx event data.
    expected_entries = (
        'Index: 1 [MRU Value 2]: C:\\looks_legit.exe '
        'Index: 2 [MRU Value 0]: Some random text here '
        'Index: 3 [MRU Value 1]: c:\\evil.exe')

    expected_event_values = {
        'data_type': 'windows:registry:mrulistex',
        'entries': expected_entries,
        'key_path': key_path,
        'last_written_time': '2012-08-28T09:23:49.0020310+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class TestMRUListExShellItemListWindowsRegistryPlugin(
    test_lib.RegistryPluginTestCase):
  """Tests for the shell item list MRUListEx plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = mrulistex.MRUListExShellItemListWindowsRegistryPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\ComDlg32\\OpenSavePidlMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\StreamMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\ComDlg32\\OpenSavePidlMRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = mrulistex.MRUListExShellItemListWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # MRUListEx event data.
    expected_entries = (
        'Index: 1 [MRU Value 1]: Shell item path: <My Computer> '
        'P:\\Application Tools\\Firefox 6.0\\Firefox Setup 6.0.exe '
        'Index: 2 [MRU Value 0]: Shell item path: <Computers and '
        'Devices> <UNKNOWN: 0x00>\\\\controller\\WebDavShare\\Firefox '
        'Setup 3.6.12.exe')

    expected_event_values = {
        'data_type': 'windows:registry:mrulistex',
        'entries': expected_entries,
        'key_path': '{0:s}\\exe'.format(key_path),
        'last_written_time': '2011-08-28T22:48:28.1593086+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 14)
    self.CheckEventData(event_data, expected_event_values)

    # Shell item event data.
    expected_event_values = {
        'accress_time': None,
        'creation_time': '2012-03-08T22:16:02+00:00',
        'data_type': 'windows:shell_item:file_entry',
        'file_reference': '44518-33',
        'long_name': 'Alloy Research',
        'name': 'ALLOYR~1',
        'modification_time': '2012-03-12T20:50:00+00:00',
        'origin': '{0:s}\\*'.format(key_path),
        'shell_item_path': (
            '<Shared Documents Folder (Users Files)> '
            '<UNKNOWN: 0x00>\\Alloy Research')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class TestMRUListExStringAndShellItemWindowsRegistryPlugin(
    test_lib.RegistryPluginTestCase):
  """Tests for the string and shell item MRUListEx plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = mrulistex.MRUListExStringAndShellItemWindowsRegistryPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\RecentDocs')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\RecentDocs')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = mrulistex.MRUListExStringAndShellItemWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # MRUListEx event data.
    expected_entries = (
        'Index: 1 [MRU Value 17]: Path: The SHIELD, '
        'Shell item: [The SHIELD.lnk] '
        'Index: 2 [MRU Value 18]: '
        'Path: captain_america_shield_by_almogrem-d48x9x8.jpg, '
        'Shell item: [captain_america_shield_by_almogrem-d48x9x8.lnk] '
        'Index: 3 [MRU Value 16]: Path: captain-america-shield-front.jpg, '
        'Shell item: [captain-america-shield-front.lnk] '
        'Index: 4 [MRU Value 12]: Path: Leadership, '
        'Shell item: [Leadership.lnk] '
        'Index: 5 [MRU Value 15]: Path: followership.pdf, '
        'Shell item: [followership.lnk] '
        'Index: 6 [MRU Value 14]: Path: leaderqualities.pdf, '
        'Shell item: [leaderqualities.lnk] '
        'Index: 7 [MRU Value 13]: Path: htlhtl.pdf, '
        'Shell item: [htlhtl.lnk] '
        'Index: 8 [MRU Value 8]: Path: StarFury, '
        'Shell item: [StarFury (2).lnk] '
        'Index: 9 [MRU Value 7]: Path: Earth_SA-26_Thunderbolt.jpg, '
        'Shell item: [Earth_SA-26_Thunderbolt.lnk] '
        'Index: 10 [MRU Value 11]: Path: 5031RR_BalancedLeadership.pdf, '
        'Shell item: [5031RR_BalancedLeadership.lnk] '
        'Index: 11 [MRU Value 10]: '
        'Path: SA-23E Mitchell-Hyundyne Starfury.docx, '
        'Shell item: [SA-23E Mitchell-Hyundyne Starfury.lnk] '
        'Index: 12 [MRU Value 9]: Path: StarFury.docx, '
        'Shell item: [StarFury (3).lnk] '
        'Index: 13 [MRU Value 6]: Path: StarFury.zip, '
        'Shell item: [StarFury.lnk] '
        'Index: 14 [MRU Value 4]: Path: VIBRANIUM.docx, '
        'Shell item: [VIBRANIUM.lnk] '
        'Index: 15 [MRU Value 5]: Path: ADAMANTIUM-Background.docx, '
        'Shell item: [ADAMANTIUM-Background.lnk] '
        'Index: 16 [MRU Value 3]: Path: Pictures, '
        'Shell item: [Pictures.lnk] '
        'Index: 17 [MRU Value 2]: Path: nick_fury_77831.jpg, '
        'Shell item: [nick_fury_77831.lnk] '
        'Index: 18 [MRU Value 1]: Path: Downloads, '
        'Shell item: [Downloads.lnk] '
        'Index: 19 [MRU Value 0]: Path: wallpaper_medium.jpg, '
        'Shell item: [wallpaper_medium.lnk]')

    expected_event_values = {
        'data_type': 'windows:registry:mrulistex',
        'entries': expected_entries,
        'key_path': key_path,
        'last_written_time': '2012-04-01T13:52:39.1137417+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class TestMRUListExStringAndShellItemListWindowsRegistryPlugin(
    test_lib.RegistryPluginTestCase):
  """Tests for the string and shell item list MRUListEx plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = mrulistex.MRUListExStringAndShellItemListWindowsRegistryPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\ComDlg32\\LastVisitedPidlMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\ComDlg32\\LastVisitedPidlMRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = mrulistex.MRUListExStringAndShellItemListWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 11)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # MRUListEx event data.
    expected_entries = (
        'Index: 1 [MRU Value 1]: Path: chrome.exe, '
        'Shell item path: <Users Libraries> <UNKNOWN: 0x00> <UNKNOWN: 0x00> '
        '<UNKNOWN: 0x00> '
        'Index: 2 [MRU Value 7]: '
        'Path: {48E1ED6B-CF49-4609-B1C1-C082BFC3D0B4}, '
        'Shell item path: <Shared Documents Folder (Users Files)> '
        '<UNKNOWN: 0x00>\\Alloy Research '
        'Index: 3 [MRU Value 6]: '
        'Path: {427865A0-03AF-4F25-82EE-10B6CB1DED3E}, '
        'Shell item path: <Users Libraries> <UNKNOWN: 0x00> <UNKNOWN: 0x00> '
        'Index: 4 [MRU Value 5]: '
        'Path: {24B5C9BB-48B5-47FF-8343-40481DBA1E2B}, '
        'Shell item path: <My Computer> C:\\Users\\nfury\\Documents '
        'Index: 5 [MRU Value 4]: '
        'Path: {0B8CFE96-DB69-4D33-8E3C-36EAB4F709E0}, '
        'Shell item path: <My Computer> C:\\Users\\nfury\\Documents\\'
        'Alloy Research '
        'Index: 6 [MRU Value 3]: '
        'Path: {D4F85F66-003D-4127-BCE9-CAD7A57B2857}, '
        'Shell item path: <Users Libraries> <UNKNOWN: 0x00> <UNKNOWN: 0x00> '
        'Index: 7 [MRU Value 0]: Path: iexplore.exe, '
        'Shell item path: <My Computer> P:\\Application Tools\\Firefox 6.0 '
        'Index: 8 [MRU Value 2]: Path: Skype.exe, '
        'Shell item path: <Users Libraries> <UNKNOWN: 0x00>')

    expected_event_values = {
        'data_type': 'windows:registry:mrulistex',
        'entries': expected_entries,
        'key_path': key_path,
        'last_written_time': '2012-04-01T13:52:38.9662902+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 10)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
