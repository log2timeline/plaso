#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MSIE Zone settings Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import msie_zones

from tests.parsers.winreg_plugins import test_lib


class MsieZoneSettingsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for Internet Settings Zones plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = msie_zones.MsieZoneSettingsPlugin()

  def testProcessNtuserLockdownZones(self):
    """Tests the Process function on a Lockdown_Zones key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Internet Settings\\Lockdown_Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 6)

    event_object = event_objects[1]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-16 21:12:40.145514')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'[1200] Run ActiveX controls and plug-ins'
    expected_value = u'3 (Not Allowed)'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_message = (
        u'[{0:s}\\0 (My Computer)] '
        u'[1200] Run ActiveX controls and plug-ins: 3 (Not Allowed) '
        u'[1400] Active scripting: 1 (Prompt User) '
        u'[CurrentLevel]: 0 '
        u'[Description]: Your computer '
        u'[DisplayName]: Computer '
        u'[Flags]: 33 '
        u'[Icon]: shell32.dll#0016 '
        u'[LowIcon]: inetcpl.cpl#005422 '
        u'[PMDisplayName]: Computer '
        u'[Protected Mode]').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testProcessNtuserZones(self):
    """Tests the Process function on a Zones key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Internet Settings\\Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 6)

    event_object = event_objects[1]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-16 21:12:40.145514')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'[1200] Run ActiveX controls and plug-ins'
    expected_value = u'0 (Allow)'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_message = (
        u'[{0:s}\\0 (My Computer)] '
        u'[1200] Run ActiveX controls and plug-ins: 0 (Allow) '
        u'[1400] Active scripting: 0 (Allow) '
        u'[2001] .NET: Run components signed with Authenticode: 3 (Not '
        u'Allowed) '
        u'[2004] .NET: Run components not signed with Authenticode: 3 (Not '
        u'Allowed) '
        u'[2007] UNKNOWN: 3 '
        u'[CurrentLevel]: 0 '
        u'[Description]: Your computer '
        u'[DisplayName]: Computer '
        u'[Flags]: 33 [Icon]: shell32.dll#0016 '
        u'[LowIcon]: inetcpl.cpl#005422 '
        u'[PMDisplayName]: Computer '
        u'[Protected Mode]').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testProcessSoftwareLockdownZones(self):
    """Tests the Process function on a Lockdown_Zones key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'SOFTWARE'])
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Internet Settings\\Lockdown_Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 6)

    event_object = event_objects[1]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-08-28 21:32:44.937675')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'[1200] Run ActiveX controls and plug-ins'
    expected_value = u'3 (Not Allowed)'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_message = (
        u'[{0:s}\\0 (My Computer)] '
        u'[1001] Download signed ActiveX controls: 1 (Prompt User) '
        u'[1004] Download unsigned ActiveX controls: 3 (Not Allowed) '
        u'[1200] Run ActiveX controls and plug-ins: 3 (Not Allowed) '
        u'[1201] Initialize and script ActiveX controls not marked as safe: 3 '
        u'(Not Allowed) '
        u'[1206] Allow scripting of IE Web browser control: 0 '
        u'[1207] Reserved: 3 '
        u'[1208] Allow previously unused ActiveX controls to run without '
        u'prompt: 3 '
        u'[1209] Allow Scriptlets: 3 '
        u'[120A] Override Per-Site (domain-based) ActiveX restrictions: 3 '
        u'[120B] Override Per-Site (domain-based) ActiveX restrictions: 0 '
        u'[1400] Active scripting: 1 (Prompt User) '
        u'[1402] Scripting of Java applets: 0 (Allow) '
        u'[1405] Script ActiveX controls marked as safe for scripting: 0 '
        u'(Allow) '
        u'[1406] Access data sources across domains: 0 (Allow) '
        u'[1407] Allow Programmatic clipboard access: 1 (Prompt User) '
        u'[1408] Reserved: 3 '
        u'[1409] UNKNOWN: 3 '
        u'[1601] Submit non-encrypted form data: 0 (Allow) '
        u'[1604] Font download: 0 (Allow) '
        u'[1605] Run Java: 0 '
        u'[1606] Userdata persistence: 0 (Allow) '
        u'[1607] Navigate sub-frames across different domains: 0 (Allow) '
        u'[1608] Allow META REFRESH: 0 (Allow) '
        u'[1609] Display mixed content: 1 (Prompt User) '
        u'[160A] Include local directory path when uploading files to a '
        u'server: 0 '
        u'[1802] Drag and drop or copy and paste files: 0 (Allow) '
        u'[1803] File Download: 0 (Allow) '
        u'[1804] Launching programs and files in an IFRAME: 0 (Allow) '
        u'[1805] Launching programs and files in webview: 0 '
        u'[1806] Launching applications and unsafe files: 0 '
        u'[1807] Reserved: 0 '
        u'[1808] Reserved: 0 '
        u'[1809] Use Pop-up Blocker: 3 (Not Allowed) '
        u'[180A] Reserved: 0 '
        u'[180C] Reserved: 0 '
        u'[180D] Reserved: 0 '
        u'[180E] UNKNOWN: 0 '
        u'[180F] UNKNOWN: 0 '
        u'[1A00] User Authentication: Logon: 0x00000000 (Automatic logon with '
        u'current user name and password) '
        u'[1A02] Allow persistent cookies that are stored on your computer: 0 '
        u'[1A03] Allow per-session cookies (not stored): 0 '
        u'[1A04] Don\'t prompt for client cert selection when no certs exists: '
        u'3 (Not Allowed) '
        u'[1A05] Allow 3rd party persistent cookies: 0 '
        u'[1A06] Allow 3rd party session cookies: 0 '
        u'[1A10] Privacy Settings: 0 '
        u'[1C00] Java permissions: 0x00000000 (Disable Java) '
        u'[2000] Binary and script behaviors: 0x00010000 '
        u'(Administrator approved) '
        u'[2005] UNKNOWN: 3 '
        u'[2100] Open files based on content, not file extension: 3 '
        u'(Not Allowed) '
        u'[2101] Web sites in less privileged zone can navigate into this '
        u'zone: 3 (Not Allowed) '
        u'[2102] Allow script initiated windows without size/position '
        u'constraints: '
        u'3 (Not Allowed) '
        u'[2103] Allow status bar updates via script: 3 '
        u'[2104] Allow websites to open windows without address or status '
        u'bars: 3 '
        u'[2105] Allow websites to prompt for information using scripted '
        u'windows: 3 '
        u'[2106] UNKNOWN: 3 '
        u'[2107] UNKNOWN: 3 '
        u'[2200] Automatic prompting for file downloads: 3 (Not Allowed) '
        u'[2201] Automatic prompting for ActiveX controls: 3 (Not Allowed) '
        u'[2301] Use Phishing Filter: 3 '
        u'[2400] .NET: XAML browser applications: 0 '
        u'[2401] .NET: XPS documents: 0 '
        u'[2402] .NET: Loose XAML: 0 '
        u'[2500] Turn on Protected Mode: 3 '
        u'[2600] Enable .NET Framework setup: 0 '
        u'[2700] UNKNOWN: 3 '
        u'[2701] UNKNOWN: 3 '
        u'[2702] UNKNOWN: 3 '
        u'[2703] UNKNOWN: 3 '
        u'[2708] UNKNOWN: 0 '
        u'[2709] UNKNOWN: 0 '
        u'[CurrentLevel]: 0 '
        u'[Description]: Your computer '
        u'[DisplayName]: Computer '
        u'[Flags]: 33 '
        u'[Icon]: shell32.dll#0016 '
        u'[LowIcon]: inetcpl.cpl#005422 '
        u'[PMDisplayName]: Computer '
        u'[Protected Mode]').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testProcessSoftwareZones(self):
    """Tests the Process function on a Zones key."""
    test_file_entry = self._GetTestFileEntryFromPath([u'SOFTWARE'])
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Internet Settings\\Zones')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 6)

    event_object = event_objects[1]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-08-28 21:32:44.937675')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'[1200] Run ActiveX controls and plug-ins'
    expected_value = u'0 (Allow)'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_message = (
        u'[{0:s}\\0 (My Computer)] '
        u'[1001] Download signed ActiveX controls: 0 (Allow) '
        u'[1004] Download unsigned ActiveX controls: 0 (Allow) '
        u'[1200] Run ActiveX controls and plug-ins: 0 (Allow) '
        u'[1201] Initialize and script ActiveX controls not marked as safe: 1 '
        u'(Prompt User) '
        u'[1206] Allow scripting of IE Web browser control: 0 '
        u'[1207] Reserved: 0 '
        u'[1208] Allow previously unused ActiveX controls to run without '
        u'prompt: 0 '
        u'[1209] Allow Scriptlets: 0 '
        u'[120A] Override Per-Site (domain-based) ActiveX restrictions: 0 '
        u'[120B] Override Per-Site (domain-based) ActiveX restrictions: 0 '
        u'[1400] Active scripting: 0 (Allow) '
        u'[1402] Scripting of Java applets: 0 (Allow) '
        u'[1405] Script ActiveX controls marked as safe for scripting: 0 '
        u'(Allow) '
        u'[1406] Access data sources across domains: 0 (Allow) '
        u'[1407] Allow Programmatic clipboard access: 0 (Allow) '
        u'[1408] Reserved: 0 '
        u'[1409] UNKNOWN: 3 '
        u'[1601] Submit non-encrypted form data: 0 (Allow) '
        u'[1604] Font download: 0 (Allow) '
        u'[1605] Run Java: 0 '
        u'[1606] Userdata persistence: 0 (Allow) '
        u'[1607] Navigate sub-frames across different domains: 0 (Allow) '
        u'[1608] Allow META REFRESH: 0 (Allow) '
        u'[1609] Display mixed content: 1 (Prompt User) '
        u'[160A] Include local directory path when uploading files to a '
        u'server: 0 '
        u'[1802] Drag and drop or copy and paste files: 0 (Allow) '
        u'[1803] File Download: 0 (Allow) '
        u'[1804] Launching programs and files in an IFRAME: 0 (Allow) '
        u'[1805] Launching programs and files in webview: 0 '
        u'[1806] Launching applications and unsafe files: 0 '
        u'[1807] Reserved: 0 '
        u'[1808] Reserved: 0 '
        u'[1809] Use Pop-up Blocker: 3 (Not Allowed) '
        u'[180A] Reserved: 0 '
        u'[180C] Reserved: 0 '
        u'[180D] Reserved: 0 '
        u'[180E] UNKNOWN: 0 '
        u'[180F] UNKNOWN: 0 '
        u'[1A00] User Authentication: Logon: 0x00000000 (Automatic logon with '
        u'current user name and password) '
        u'[1A02] Allow persistent cookies that are stored on your computer: 0 '
        u'[1A03] Allow per-session cookies (not stored): 0 '
        u'[1A04] Don\'t prompt for client cert selection when no certs exists: '
        u'0 (Allow) '
        u'[1A05] Allow 3rd party persistent cookies: 0 '
        u'[1A06] Allow 3rd party session cookies: 0 '
        u'[1A10] Privacy Settings: 0 '
        u'[1C00] Java permissions: 0x00020000 (Medium safety) '
        u'[2000] Binary and script behaviors: 0 (Allow) '
        u'[2001] .NET: Run components signed with Authenticode: '
        u'3 (Not Allowed) '
        u'[2004] .NET: Run components not signed with Authenticode: '
        u'3 (Not Allowed) '
        u'[2005] UNKNOWN: 0 '
        u'[2007] UNKNOWN: 3 '
        u'[2100] Open files based on content, not file extension: 0 (Allow) '
        u'[2101] Web sites in less privileged zone can navigate into this '
        u'zone: 3 (Not Allowed) '
        u'[2102] Allow script initiated windows without size/position '
        u'constraints: 0 (Allow) '
        u'[2103] Allow status bar updates via script: 0 '
        u'[2104] Allow websites to open windows without address or status '
        u'bars: 0 '
        u'[2105] Allow websites to prompt for information using scripted '
        u'windows: 0 '
        u'[2106] UNKNOWN: 0 '
        u'[2107] UNKNOWN: 0 '
        u'[2200] Automatic prompting for file downloads: 0 (Allow) '
        u'[2201] Automatic prompting for ActiveX controls: 0 (Allow) '
        u'[2300] Allow web pages to use restricted protocols for active '
        u'content: 1 (Prompt User) '
        u'[2301] Use Phishing Filter: 3 '
        u'[2400] .NET: XAML browser applications: 0 '
        u'[2401] .NET: XPS documents: 0 '
        u'[2402] .NET: Loose XAML: 0 '
        u'[2500] Turn on Protected Mode: 3 '
        u'[2600] Enable .NET Framework setup: 0 '
        u'[2700] UNKNOWN: 3 '
        u'[2701] UNKNOWN: 0 '
        u'[2702] UNKNOWN: 3 '
        u'[2703] UNKNOWN: 3 '
        u'[2708] UNKNOWN: 0 '
        u'[2709] UNKNOWN: 0 '
        u'[CurrentLevel]: 0 '
        u'[Description]: Your computer '
        u'[DisplayName]: Computer '
        u'[Flags]: 33 '
        u'[Icon]: shell32.dll#0016 '
        u'[LowIcon]: inetcpl.cpl#005422 '
        u'[PMDisplayName]: Computer '
        u'[Protected Mode]').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
