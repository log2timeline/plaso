#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MSIE zone settings Windows Registry plugin."""

import unittest

from plaso.parsers.winreg_plugins import msie_zones

from tests.parsers.winreg_plugins import test_lib


class MSIEZoneSettingsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for Internet Settings zone settings plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = msie_zones.MSIEZoneSettingsPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Lockdown_Zones')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Zones')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Lockdown_Zones')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Zones')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  def testProcessNtuserLockdownZones(self):
    """Tests the Process function on a Lockdown_Zones key."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Lockdown_Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = msie_zones.MSIEZoneSettingsPlugin()
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

    expected_settings = (
        '[1200] Run ActiveX controls and plug-ins: 3 (Not Allowed) '
        '[1400] Active scripting: 1 (Prompt User) '
        '[CurrentLevel]: 0 '
        '[Description]: Your computer '
        '[DisplayName]: Computer '
        '[Flags]: 33 '
        '[Icon]: shell32.dll#0016 '
        '[LowIcon]: inetcpl.cpl#005422 '
        '[PMDisplayName]: Computer '
        '[Protected Mode]')

    expected_event_values = {
        'data_type': 'windows:registry:msie_zone_settings',
        'key_path': '{0:s}\\0 (My Computer)'.format(key_path),
        'last_written_time': '2011-09-16T21:12:40.1455141+00:00',
        'settings': expected_settings}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessNtuserZones(self):
    """Tests the Process function on a Zones key."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = msie_zones.MSIEZoneSettingsPlugin()
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

    expected_settings = (
        '[1200] Run ActiveX controls and plug-ins: 0 (Allow) '
        '[1400] Active scripting: 0 (Allow) '
        '[2001] .NET: Run components signed with Authenticode: 3 (Not '
        'Allowed) '
        '[2004] .NET: Run components not signed with Authenticode: 3 (Not '
        'Allowed) '
        '[2007] UNKNOWN: 3 '
        '[CurrentLevel]: 0 '
        '[Description]: Your computer '
        '[DisplayName]: Computer '
        '[Flags]: 33 [Icon]: shell32.dll#0016 '
        '[LowIcon]: inetcpl.cpl#005422 '
        '[PMDisplayName]: Computer '
        '[Protected Mode]')

    expected_event_values = {
        'data_type': 'windows:registry:msie_zone_settings',
        'key_path': '{0:s}\\0 (My Computer)'.format(key_path),
        'last_written_time': '2011-09-16T21:12:40.1455141+00:00',
        'settings': expected_settings}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessSoftwareLockdownZones(self):
    """Tests the Process function on a Lockdown_Zones key."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE'])
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Lockdown_Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = msie_zones.MSIEZoneSettingsPlugin()
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

    expected_settings = (
        '[1001] Download signed ActiveX controls: 1 (Prompt User) '
        '[1004] Download unsigned ActiveX controls: 3 (Not Allowed) '
        '[1200] Run ActiveX controls and plug-ins: 3 (Not Allowed) '
        '[1201] Initialize and script ActiveX controls not marked as safe: 3 '
        '(Not Allowed) '
        '[1206] Allow scripting of IE Web browser control: 0 '
        '[1207] Reserved: 3 '
        '[1208] Allow previously unused ActiveX controls to run without '
        'prompt: 3 '
        '[1209] Allow Scriptlets: 3 '
        '[120A] Override Per-Site (domain-based) ActiveX restrictions: 3 '
        '[120B] Override Per-Site (domain-based) ActiveX restrictions: 0 '
        '[1400] Active scripting: 1 (Prompt User) '
        '[1402] Scripting of Java applets: 0 (Allow) '
        '[1405] Script ActiveX controls marked as safe for scripting: 0 '
        '(Allow) '
        '[1406] Access data sources across domains: 0 (Allow) '
        '[1407] Allow Programmatic clipboard access: 1 (Prompt User) '
        '[1408] Reserved: 3 '
        '[1409] UNKNOWN: 3 '
        '[1601] Submit non-encrypted form data: 0 (Allow) '
        '[1604] Font download: 0 (Allow) '
        '[1605] Run Java: 0 '
        '[1606] Userdata persistence: 0 (Allow) '
        '[1607] Navigate sub-frames across different domains: 0 (Allow) '
        '[1608] Allow META REFRESH: 0 (Allow) '
        '[1609] Display mixed content: 1 (Prompt User) '
        '[160A] Include local directory path when uploading files to a '
        'server: 0 '
        '[1802] Drag and drop or copy and paste files: 0 (Allow) '
        '[1803] File Download: 0 (Allow) '
        '[1804] Launching programs and files in an IFRAME: 0 (Allow) '
        '[1805] Launching programs and files in webview: 0 '
        '[1806] Launching applications and unsafe files: 0 '
        '[1807] Reserved: 0 '
        '[1808] Reserved: 0 '
        '[1809] Use Pop-up Blocker: 3 (Not Allowed) '
        '[180A] Reserved: 0 '
        '[180C] Reserved: 0 '
        '[180D] Reserved: 0 '
        '[180E] UNKNOWN: 0 '
        '[180F] UNKNOWN: 0 '
        '[1A00] User Authentication: Logon: 0x00000000 (Automatic logon with '
        'current user name and password) '
        '[1A02] Allow persistent cookies that are stored on your computer: 0 '
        '[1A03] Allow per-session cookies (not stored): 0 '
        '[1A04] Don\'t prompt for client cert selection when no certs exists: '
        '3 (Not Allowed) '
        '[1A05] Allow 3rd party persistent cookies: 0 '
        '[1A06] Allow 3rd party session cookies: 0 '
        '[1A10] Privacy Settings: 0 '
        '[1C00] Java permissions: 0x00000000 (Disable Java) '
        '[2000] Binary and script behaviors: 0x00010000 '
        '(Administrator approved) '
        '[2005] UNKNOWN: 3 '
        '[2100] Open files based on content, not file extension: 3 '
        '(Not Allowed) '
        '[2101] Web sites in less privileged zone can navigate into this '
        'zone: 3 (Not Allowed) '
        '[2102] Allow script initiated windows without size/position '
        'constraints: '
        '3 (Not Allowed) '
        '[2103] Allow status bar updates via script: 3 '
        '[2104] Allow websites to open windows without address or status '
        'bars: 3 '
        '[2105] Allow websites to prompt for information using scripted '
        'windows: 3 '
        '[2106] UNKNOWN: 3 '
        '[2107] UNKNOWN: 3 '
        '[2200] Automatic prompting for file downloads: 3 (Not Allowed) '
        '[2201] Automatic prompting for ActiveX controls: 3 (Not Allowed) '
        '[2301] Use Phishing Filter: 3 '
        '[2400] .NET: XAML browser applications: 0 '
        '[2401] .NET: XPS documents: 0 '
        '[2402] .NET: Loose XAML: 0 '
        '[2500] Turn on Protected Mode: 3 '
        '[2600] Enable .NET Framework setup: 0 '
        '[2700] UNKNOWN: 3 '
        '[2701] UNKNOWN: 3 '
        '[2702] UNKNOWN: 3 '
        '[2703] UNKNOWN: 3 '
        '[2708] UNKNOWN: 0 '
        '[2709] UNKNOWN: 0 '
        '[CurrentLevel]: 0 '
        '[Description]: Your computer '
        '[DisplayName]: Computer '
        '[Flags]: 33 '
        '[Icon]: shell32.dll#0016 '
        '[LowIcon]: inetcpl.cpl#005422 '
        '[PMDisplayName]: Computer '
        '[Protected Mode]')

    expected_event_values = {
        'data_type': 'windows:registry:msie_zone_settings',
        'key_path': '{0:s}\\0 (My Computer)'.format(key_path),
        'last_written_time': '2011-08-28T21:32:44.9376751+00:00',
        'settings': expected_settings}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessSoftwareZones(self):
    """Tests the Process function on a Zones key."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE'])
    key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Internet Settings\\Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = msie_zones.MSIEZoneSettingsPlugin()
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

    expected_settings = (
        '[1001] Download signed ActiveX controls: 0 (Allow) '
        '[1004] Download unsigned ActiveX controls: 0 (Allow) '
        '[1200] Run ActiveX controls and plug-ins: 0 (Allow) '
        '[1201] Initialize and script ActiveX controls not marked as safe: 1 '
        '(Prompt User) '
        '[1206] Allow scripting of IE Web browser control: 0 '
        '[1207] Reserved: 0 '
        '[1208] Allow previously unused ActiveX controls to run without '
        'prompt: 0 '
        '[1209] Allow Scriptlets: 0 '
        '[120A] Override Per-Site (domain-based) ActiveX restrictions: 0 '
        '[120B] Override Per-Site (domain-based) ActiveX restrictions: 0 '
        '[1400] Active scripting: 0 (Allow) '
        '[1402] Scripting of Java applets: 0 (Allow) '
        '[1405] Script ActiveX controls marked as safe for scripting: 0 '
        '(Allow) '
        '[1406] Access data sources across domains: 0 (Allow) '
        '[1407] Allow Programmatic clipboard access: 0 (Allow) '
        '[1408] Reserved: 0 '
        '[1409] UNKNOWN: 3 '
        '[1601] Submit non-encrypted form data: 0 (Allow) '
        '[1604] Font download: 0 (Allow) '
        '[1605] Run Java: 0 '
        '[1606] Userdata persistence: 0 (Allow) '
        '[1607] Navigate sub-frames across different domains: 0 (Allow) '
        '[1608] Allow META REFRESH: 0 (Allow) '
        '[1609] Display mixed content: 1 (Prompt User) '
        '[160A] Include local directory path when uploading files to a '
        'server: 0 '
        '[1802] Drag and drop or copy and paste files: 0 (Allow) '
        '[1803] File Download: 0 (Allow) '
        '[1804] Launching programs and files in an IFRAME: 0 (Allow) '
        '[1805] Launching programs and files in webview: 0 '
        '[1806] Launching applications and unsafe files: 0 '
        '[1807] Reserved: 0 '
        '[1808] Reserved: 0 '
        '[1809] Use Pop-up Blocker: 3 (Not Allowed) '
        '[180A] Reserved: 0 '
        '[180C] Reserved: 0 '
        '[180D] Reserved: 0 '
        '[180E] UNKNOWN: 0 '
        '[180F] UNKNOWN: 0 '
        '[1A00] User Authentication: Logon: 0x00000000 (Automatic logon with '
        'current user name and password) '
        '[1A02] Allow persistent cookies that are stored on your computer: 0 '
        '[1A03] Allow per-session cookies (not stored): 0 '
        '[1A04] Don\'t prompt for client cert selection when no certs exists: '
        '0 (Allow) '
        '[1A05] Allow 3rd party persistent cookies: 0 '
        '[1A06] Allow 3rd party session cookies: 0 '
        '[1A10] Privacy Settings: 0 '
        '[1C00] Java permissions: 0x00020000 (Medium safety) '
        '[2000] Binary and script behaviors: 0 (Allow) '
        '[2001] .NET: Run components signed with Authenticode: '
        '3 (Not Allowed) '
        '[2004] .NET: Run components not signed with Authenticode: '
        '3 (Not Allowed) '
        '[2005] UNKNOWN: 0 '
        '[2007] UNKNOWN: 3 '
        '[2100] Open files based on content, not file extension: 0 (Allow) '
        '[2101] Web sites in less privileged zone can navigate into this '
        'zone: 3 (Not Allowed) '
        '[2102] Allow script initiated windows without size/position '
        'constraints: 0 (Allow) '
        '[2103] Allow status bar updates via script: 0 '
        '[2104] Allow websites to open windows without address or status '
        'bars: 0 '
        '[2105] Allow websites to prompt for information using scripted '
        'windows: 0 '
        '[2106] UNKNOWN: 0 '
        '[2107] UNKNOWN: 0 '
        '[2200] Automatic prompting for file downloads: 0 (Allow) '
        '[2201] Automatic prompting for ActiveX controls: 0 (Allow) '
        '[2300] Allow web pages to use restricted protocols for active '
        'content: 1 (Prompt User) '
        '[2301] Use Phishing Filter: 3 '
        '[2400] .NET: XAML browser applications: 0 '
        '[2401] .NET: XPS documents: 0 '
        '[2402] .NET: Loose XAML: 0 '
        '[2500] Turn on Protected Mode: 3 '
        '[2600] Enable .NET Framework setup: 0 '
        '[2700] UNKNOWN: 3 '
        '[2701] UNKNOWN: 0 '
        '[2702] UNKNOWN: 3 '
        '[2703] UNKNOWN: 3 '
        '[2708] UNKNOWN: 0 '
        '[2709] UNKNOWN: 0 '
        '[CurrentLevel]: 0 '
        '[Description]: Your computer '
        '[DisplayName]: Computer '
        '[Flags]: 33 '
        '[Icon]: shell32.dll#0016 '
        '[LowIcon]: inetcpl.cpl#005422 '
        '[PMDisplayName]: Computer '
        '[Protected Mode]')

    expected_event_values = {
        'data_type': 'windows:registry:msie_zone_settings',
        'key_path': '{0:s}\\0 (My Computer)'.format(key_path),
        'last_written_time': '2011-08-28T21:32:44.9376751+00:00',
        'settings': expected_settings}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
