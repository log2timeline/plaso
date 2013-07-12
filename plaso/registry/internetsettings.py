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
"""This file is a Internet Settings parser for Windows registry."""

import logging

from plaso.lib import event
from plaso.lib import win_registry_interface


__author__ = 'Elizabeth Schweinsberg (beth@bethlogic.net)'


class InternetSettingsZonesBase(win_registry_interface.KeyPlugin):
  """Base class for formatting the Internet Settings-Zones."""

  __abstract = True

  URLS = ['http://support.microsoft.com/kb/182569']

  ZONE_NAMES = {
    '0': '0 (My Computer)',
    '1': '1 (Local Intranet Zone)',
    '2': '2 (Trusted sites Zone)',
    '3': '3 (Internet Zone)',
    '4': '4 (Restricted Sites Zone)',
    '5': '5 (Custom)'
  }

  PERMISSIONS = {
    '0': '0 (Allow)',
    '1': '1 (Prompt User)',
    '3': '3 (Not Allowed)'
  }

  ACTIONS = {
    '1200': 'Run ActiveX controls and plug-ins',
    '1400': 'Active scripting',
    '1001': 'Download signed ActiveX controls',
    '1004': 'Download unsigned ActiveX controls',
    '1201': 'Initialize and script ActiveX controls not marked as safe',
    '1206': 'Allow scripting of IE Web browser control',
    '1207': 'Reserved',
    '1208': 'Allow previously unused ActiveX controls to run without prompt',
    '1209': 'Allow Scriptlets',
    '120A': 'Override Per-Site (domain-based) ActiveX restrictions',
    '120B': 'Override Per-Site (domain-based) ActiveX restrictions',
    '1402': 'Scripting of Java applets',
    '1405': 'Script ActiveX controls marked as safe for scripting',
    '1406': 'Access data sources across domains',
    '1407': 'Allow Programmatic clipboard access',
    '1408': 'Reserved',
    '1601': 'Submit non-encrypted form data',
    '1604': 'Font download',
    '1605': 'Run Java',
    '1606': 'Userdata persistence',
    '1607': 'Navigate sub-frames across different domains',
    '1608': 'Allow META REFRESH',
    '1609': 'Display mixed content',
    '160A': 'Include local directory path when uploading files to a server',
    '1800': 'Installation of desktop items',
    '1802': 'Drag and drop or copy and paste files',
    '1803': 'File Download',
    '1804': 'Launching programs and files in an IFRAME',
    '1805': 'Launching programs and files in webview',
    '1806': 'Launching applications and unsafe files',
    '1807': 'Reserved',
    '1808': 'Reserved',
    '1809': 'Use Pop-up Blocker',
    '180A': 'Reserved',
    '180B': 'Reserved',
    '180C': 'Reserved',
    '180D': 'Reserved',
    '1A00': 'User Authentication: Logon',
    '1A02': 'Allow persistent cookies that are stored on your computer',
    '1A03': 'Allow per-session cookies (not stored)',
    '1A04': 'Don\'t prompt for client cert selection when no certs exists',
    '1A05': 'Allow 3rd party persistent cookies',
    '1A06': 'Allow 3rd party session cookies',
    '1A10': 'Privacy Settings',
    '1C00': 'Java permissions',
    '1E05': 'Software channel permissions',
    '1F00': 'Reserved',
    '2000': 'Binary and script behaviors',
    '2001': '.NET: Run components signed with Authenticode',
    '2004': '.NET: Run components not signed with Authenticode',
    '2100': 'Open files based on content, not file extension',
    '2101': 'Web sites in less privileged zone can navigate into this zone',
    '2102': 'Allow script initiated windows without size/position constraints',
    '2103': 'Allow status bar updates via script',
    '2104': 'Allow websites to open windows without address or status bars',
    '2105': 'Allow websites to prompt for information using scripted windows',
    '2200': 'Automatic prompting for file downloads',
    '2201': 'Automatic prompting for ActiveX controls',
    '2300': 'Allow web pages to use restricted protocols for active content',
    '2301': 'Use Phishing Filter',
    '2400': '.NET: XAML browser applications',
    '2401': '.NET: XPS documents',
    '2402': '.NET: Loose XAML',
    '2500': 'Turn on Protected Mode',
    '2600': 'Enable .NET Framework setup',
    '{AEBA21FA-782A-4A90-978D-B72164C80120}': 'First Party Cookie',
    '{A8A88C49-5EB2-4990-A1A2-0876022C854F}': 'Third Party Cookie'
  }

  def GetEntries(self):
    """Add info to the values of the the Internet Settings Zones."""
    # Store values of the Internet Settings/[Lockdown_]Zones key.
    text_dict = {}
    for value in self._key.GetValues():
      if not value.name:
        continue
      text_dict[value.name] = value.GetData(unicode)

    if not text_dict:
      text_dict[u'Value'] = u'No values stored in key'
    reg_evt = event.WinRegistryEvent(
        self._key.path, text_dict, self._key.timestamp)
    reg_evt.offset = self._key.offset
    yield reg_evt

    # REGALERT if there are no Zone SubKeys.
    if not self._key.HasSubkeys():
      logging.info('No Subkeys for Internet Settings/Zones')
      text_dict = {
        'Zone Subkeys': 'REGALERT No Zones set for Internet Settings'
      }

      reg_evt = event.WinRegistryEvent(
          self._key.path, text_dict, self._key.timestamp)
      reg_evt.offset = self._key.offset
      yield reg_evt
      return

    # Process the Zones.
    for zone in self._key.GetSubkeys():
      path = u'%s\\%s' % (self._key.path, self.ZONE_NAMES[zone.name])
      text_dict = {}
      for value in zone.GetValues():
        if not value.name:
          continue
        # Matched and Unmatched actions need the data parsed the same way.
        data_type = value.GetTypeStr()
        if 'DWORD' in data_type or 'SZ' in data_type:
          data = value.GetData(unicode)
        else:
          # Some values contain BINARY data, default plugin prints this way.
          data = u'[DATA TYPE %s]' % data_type

        # Now see if we know what Action the Zone is setting.
        action = u'[{}] {}'.format(value.name,
                                   self.ACTIONS.get(value.name, ''))
        # TODO(eschwein) some actions have more complicated permissions.
        data_value = self.PERMISSIONS.get(data, data)
        text_dict[action] = data_value
      reg_evt = event.WinRegistryEvent(path, text_dict, zone.timestamp)
      yield reg_evt


class InternetSettingsZonesNtuserPlugin(InternetSettingsZonesBase):
  """Gathers and formats the NTUser settings for Internet Settings-Zones."""

  REG_TYPE = 'NTUSER'
  REG_KEY = ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
             '\\Zones')


class InternetSettingsLockdownZonesNtuserPlugin(InternetSettingsZonesBase):
  """Formats the NTUser settings for Internet Settings-Lockdown_Zones."""

  REG_TYPE = 'NTUSER'
  REG_KEY = ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
             '\\Lockdown_Zones')


class InternetSettingsZonesSoftwarePlugin(InternetSettingsZonesBase):
  """Gathers and formats the Software settings for Internet Settings-Zones."""

  REG_TYPE = 'SOFTWARE'
  REG_KEY = '\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones'


class InternetSettingsLockdownZonesSoftwarePlugin(InternetSettingsZonesBase):
  """Formats the Software settings for Internet Settings-Lockdown_Zones."""

  REG_TYPE = 'SOFTWARE'
  REG_KEY = ('\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'
             '\\Lockdown_Zones')


