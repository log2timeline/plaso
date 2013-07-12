#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a test for Internet Settings formatting in Plaso."""
import os
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.registry import internetsettings
from plaso.winreg import winpyregf


class RegistrySoftwareZonesTest(unittest.TestCase):
  """The unit test for Internet Settings formatting."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'SOFTWARE')
    file_object = open(test_file, 'rb')
    # TODO: create a factory not have a specific back-end implementation
    # directly invoked here.
    self.registry = winpyregf.WinRegistry(file_object)

  def testInternetSettingsZonesSoftware(self):
    """Test the Internet Settings Zones plugin for the Software hive."""
    key = self.registry.GetKey(
        '\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones')
    plugin = internetsettings.InternetSettingsZonesSoftwarePlugin(
        None, None, None)
    entries = list(plugin.Process(key))

    line = (u'[\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones\\'
            '0 (My Computer)] [1001] Download signed ActiveX controls: 0 (Allow'
            ') [1004] Download unsigned ActiveX controls: 0 (Allow) [1200] Run'
            ' ActiveX controls and plug-ins: 0 (Allow) [1201] Initialize and'
            ' script ActiveX controls not marked as safe: 1 (Prompt User) [1206'
            '] Allow scripting of IE Web browser control: 0 (Allow) [1207]'
            ' Reserved: 0 (Allow) [1208] Allow previously unused ActiveX contro'
            'ls to run without prompt: 0 (Allow) [1209] Allow Scriptlets: 0 (Al'
            'low) [120A] Override Per-Site (domain-based) ActiveX restrictions:'
            ' 0 (Allow) [120B] Override Per-Site (domain-based) ActiveX'
            ' restrictions: 0 (Allow) [1400] Active scripting: 0 (Allow) [1402]'
            ' Scripting of Java applets: 0 (Allow) [1405] Script ActiveX contro'
            'ls marked as safe for scripting: 0 (Allow) [1406] Access data sour'
            'ces across domains: 0 (Allow)')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1314567164937675)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'0 (Allow)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg[0:len(line)], line)


class RegistrySoftwareLockdownZonesTest(unittest.TestCase):
  """The unit test for Internet Settings/Lockdown_Zones formatting."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'SOFTWARE')
    file_object = open(test_file, 'rb')
    # TODO: create a factory not have a specific back-end implementation
    # directly invoked here.
    self.registry = winpyregf.WinRegistry(file_object)

  def testInternetSettingsLockdownZonesSoftware(self):
    """Test the Internet Settings Lockdown Zones plugin for Software hive."""
    key = self.registry.GetKey(
        '\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
        '\\Lockdown_Zones')
    plugin = internetsettings.InternetSettingsLockdownZonesSoftwarePlugin(
        None, None, None)
    entries = list(plugin.Process(key))

    line = (u'[\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\'
            'Lockdown_Zones\\0 (My Computer)] [1001] Download signed ActiveX'
            ' controls: 1 (Prompt User) [1004] Download unsigned ActiveX contro'
            'ls: 3 (Not Allowed) [1200] Run ActiveX controls and plug-ins: 3 (N'
            'ot Allowed) [1201] Initialize and script ActiveX controls not mark'
            'ed as safe: 3 (Not Allowed) [1206] Allow scripting of IE Web brows'
            'er control: 0 (Allow) [1207] Reserved: 3 (Not Allowed) [1208] Allo'
            'w previously unused ActiveX controls to run without prompt: 3 (Not'
            ' Allowed) [1209] Allow Scriptlets: 3 (Not Allowed) [120A] Override'
            ' Per-Site (domain-based) ActiveX restrictions: 3 (Not Allowed) [12'
            '0B] Override Per-Site (domain-based) ActiveX restrictions: 0 (Allo'
            'w) [1400] Active scripting: 1 (Prompt User) [1402] Scripting of Ja'
            'va applets: 0 (Allow) [1405] Script ActiveX controls marked as saf'
            'e for scripting: 0 (Allow) [1406] Access data sources across domai'
            'ns: 0 (Allow) [1407] Allow Programmatic clipboard access: 1 (Promp'
            't User) [1408] Reserved: 3 (Not Allowed) [1409] : 3 (Not Allowed)')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1314567164937675)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'3 (Not Allowed)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg[0:len(line)], line)


class RegistryNtuserZonesTest(unittest.TestCase):
  """The unit test for Internet Settings formatting."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_object = open(test_file, 'rb')
    # TODO: create a factory not have a specific back-end implementation
    # directly invoked here.
    self.registry = winpyregf.WinRegistry(file_object)

  def testInternetSettingsZonesNtuser(self):
    """Test the Internet Settings Zones plugin for the NTUser hive."""
    key = self.registry.GetKey(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
        '\\Zones')
    plugin = internetsettings.InternetSettingsZonesNtuserPlugin(
        None, None, None)
    entries = list(plugin.Process(key))

    line = (u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet'
            ' Settings\\Zones\\0 (My Computer)] [1200] Run ActiveX contro'
            'ls and plug-ins: 0 (Allow) [1400] Active scripting: 0 (Allow) [200'
            '1] .NET: Run components signed with Authenticode: 3 (Not Allowed)'
            ' [2004] .NET: Run components not signed with Authenticode: 3 (Not'
            ' Allowed) [2007] : 3 (Not Allowed) [CurrentLevel] : 0 (Allow) [Des'
            'cription] : Your computer [DisplayName] : Computer [Flags] : 33 [I'
            'con] : shell32.dll#0016 [LowIcon] : inetcpl.cpl#005422 [PMDisplayN'
            'ame] : Computer [Protected Mode]')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1316207560145514)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'0 (Allow)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg[0:len(line)], line)


class RegistryNtuserLockdownZonesTest(unittest.TestCase):
  """The unit test for Internet Settings formatting."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_object = open(test_file, 'rb')
    # TODO: create a factory not have a specific back-end implementation
    # directly invoked here.
    self.registry = winpyregf.WinRegistry(file_object)

  def testInternetSettingsLockdownZonesNtuser(self):
    """Test the Internet Settings Lockdown Zones plugin for the NTUser hive."""
    key = self.registry.GetKey(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
        '\\Lockdown_Zones')
    plugin = internetsettings.InternetSettingsLockdownZonesNtuserPlugin(
        None, None, None)
    entries = list(plugin.Process(key))

    line = (u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet'
            ' Settings\\Lockdown_Zones\\0 (My Computer)] [1200] Run ActiveX'
            ' controls and plug-ins: 3 (Not Allowed) [1400] Active scripting: 1'
            ' (Prompt User) [CurrentLevel] : 0 (Allow) [Description] : Your'
            ' computer [DisplayName] : Computer [Flags] : 33 [Icon] :'
            ' shell32.dll#0016 [LowIcon] : inetcpl.cpl#005422 [PMDisplayName] :'
            ' Computer [Protected Mode]')

    # [1200] Run ActiveX controls and plug-ins: Allow (0)
    self.assertEquals(entries[1].timestamp, 1316207560145514)
    self.assertTrue(
        u'[1200] Run ActiveX controls and plug-ins' in entries[1].regvalue)
    self.assertEquals(
        entries[1].regvalue[u'[1200] Run ActiveX controls and plug-ins'],
        u'3 (Not Allowed)')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg, line)


if __name__ == '__main__':
  unittest.main()
