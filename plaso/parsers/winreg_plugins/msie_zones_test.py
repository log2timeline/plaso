#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the tests for the MSIE Zone settings plugin."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import msie_zones
from plaso.pvfs import utils
from plaso.winreg import winregistry


class SoftwareMsieZoneSettingsPluginTest(unittest.TestCase):
  """The unit test for MSIE Zone settings plugin in the Software hive."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'SOFTWARE')
    file_entry = utils.OpenOSFileEntry(test_file)
    self.winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testMsieZoneSettingsSoftwareZonesPlugin(self):
    """Test the Internet Settings Zones plugin for the Software hive."""
    key = self.winreg_file.GetKeyByPath(
        '\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones')
    plugin = msie_zones.MsieZoneSettingsSoftwareZonesPlugin()
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones\\0 '
        u'(My Computer)] '
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
        u'[1406] Access data sources across domains: 0 (Allow)')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1314567164937675)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'0 (Allow)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg[0:len(expected_line)], expected_line)

  def testMsieZoneSettingsSoftwareLockdownZonesPlugin(self):
    """Test the Internet Settings Lockdown Zones plugin for Software hive."""
    key = self.winreg_file.GetKeyByPath(
        '\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
        '\\Lockdown_Zones')
    plugin = msie_zones.MsieZoneSettingsSoftwareLockdownZonesPlugin()
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\'
        u'Lockdown_Zones\\0 (My Computer)] '
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
        u'[1409] UNKNOWN: 3')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1314567164937675)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'3 (Not Allowed)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg[0:len(expected_line)], expected_line)


class UserMsieZoneSettingsPluginTest(unittest.TestCase):
  """The unit test for MSIE Zone settings plugin in the User hive."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_entry = utils.OpenOSFileEntry(test_file)
    self.winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testMsieZoneSettingsUserZonesPlugin(self):
    """Test the plugin for the Zones."""
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
        '\\Zones')
    plugin = msie_zones.MsieZoneSettingsUserZonesPlugin()
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet '
        u'Settings\\Zones\\0 (My Computer)] '
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
        u'[Protected Mode]')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1316207560145514)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'0 (Allow)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg[0:len(expected_line)], expected_line)

  def testMsieZoneSettingsUserLockdownZonesPlugin(self):
    """Test the plugin for the Lockdown Zones."""
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
        '\\Lockdown_Zones')
    plugin = msie_zones.MsieZoneSettingsUserLockdownZonesPlugin()
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet '
        u'Settings\\Lockdown_Zones\\0 (My Computer)] '
        u'[1200] Run ActiveX controls and plug-ins: 3 (Not Allowed) '
        u'[1400] Active scripting: 1 (Prompt User) '
        u'[CurrentLevel]: 0 '
        u'[Description]: Your computer '
        u'[DisplayName]: Computer '
        u'[Flags]: 33 '
        u'[Icon]: shell32.dll#0016 '
        u'[LowIcon]: inetcpl.cpl#005422 '
        u'[PMDisplayName]: Computer '
        u'[Protected Mode]')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1316207560145514)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'3 (Not Allowed)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg, expected_line)


if __name__ == '__main__':
  unittest.main()
