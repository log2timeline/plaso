#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
# limitations under the  License.
"""This file contains preprocessors for Windows."""

import logging

from plaso.lib import preprocess_interface
from plaso.winreg import utils


class WinGetSystemPath(preprocess_interface.PreprocessGetPath):
  """Get the system path."""
  SUPPORTED_OS = ['Windows']
  ATTRIBUTE = 'systemroot'
  PATH = '(Windows|WinNT)/System32'


class WinGetWinDirPath(preprocess_interface.PreprocessGetPath):
  """Get the system path."""
  SUPPORTED_OS = ['Windows']
  ATTRIBUTE = 'windir'
  PATH = '(Windows|WinNT|WINNT35|WTSRV)'


class WinGetRegistryPath(preprocess_interface.PreprocessGetPath):
  """Get the system registry path."""
  SUPPORTED_OS = ['Windows']
  ATTRIBUTE = 'sysregistry'
  PATH = '(Windows|WinNT)/System32/config'


class WinVersion(preprocess_interface.WinRegistryPreprocess):
  """Fetch information about the current Windows version."""

  ATTRIBUTE = 'osversion'

  REGFILE = 'SOFTWARE'
  REG_KEY = '\\Microsoft\\Windows NT\\CurrentVersion'

  def ParseKey(self, key):
    """Extract the version information from the key."""
    value = key.GetValue('ProductName')
    if value:
      return u'{}'.format(value.data)


class WinUsers(preprocess_interface.WinRegistryPreprocess):
  """Fetch information about user profiles."""

  ATTRIBUTE = 'users'

  REG_FILE = 'SOFTWARE'
  REG_KEY = '\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList'

  def ParseKey(self, key):
    """Extract current control set information."""
    users = []

    for sid in key.GetSubkeys():
      user = {}
      user['sid'] = sid.name
      value = sid.GetValue('ProfileImagePath')
      if value:
        user['path'] = value.data
        user['name'] = utils.WinRegBasename(user['path'])

      users.append(user)

    return users


class WinHostName(preprocess_interface.WinRegistryPreprocess):
  """A preprocessing class that fetches the hostname information."""

  ATTRIBUTE = 'hostname'

  # Depend upon the current control set to be found.
  WEIGHT = 3

  REG_KEY = '{current_control_set}\\Control\\ComputerName\\ComputerName'
  REG_FILE = 'SYSTEM'

  def ParseKey(self, key):
    """Extract the hostname from the registry."""
    value = key.GetValue('ComputerName')
    if value and type(value.data) == unicode:
      return value.data


class WinRegCodePage(preprocess_interface.WinRegistryPreprocess):
  """A preprocessing class that fetches codepage information."""

  # Defines the preprocess attribute to be set.
  ATTRIBUTE = 'code_page'

  # Depend upon the current control set, thus lower the priority.
  WEIGHT = 3

  REG_KEY = '{current_control_set}\\Control\\Nls\\CodePage'
  REG_FILE = 'SYSTEM'

  def ParseKey(self, key):
    """Retrieves the codepage or cp1252 by default."""
    value = key.GetValue('ACP')
    if value and type(value.data) == unicode:
      return u'cp{0:s}'.format(value.data)

    logging.warning('Unable to determine ASCII string codepage, '
                    'defaulting to cp1252.')
    return 'cp1252'


class WinRegTimeZone(preprocess_interface.WinRegistryPreprocess):
  """A preprocessing class that fetches timezone information."""

  # Defines the preprocess attribute to be set.
  ATTRIBUTE = 'time_zone_str'

  # Depend upon the current control set, thus lower the priority.
  WEIGHT = 3

  REG_KEY = '{current_control_set}\\Control\\TimeZoneInformation'
  REG_FILE = 'SYSTEM'

  # transform gathered from these sources:
  # Prebuilt from HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows N\
  #    T\CurrentVersion\Time Zones\
  ZONE_LIST = {
      'IndiaStandardTime': 'Asia/Kolkata',
      'EasternStandardTime': 'EST5EDT',
      'EasternDaylightTime': 'EST5EDT',
      'MountainStandardTime': 'MST7MDT',
      'MountainDaylightTime': 'MST7MDT',
      'PacificStandardTime': 'PST8PDT',
      'PacificDaylightTime': 'PST8PDT',
      'CentralStandardTime': 'CST6CDT',
      'CentralDaylightTime': 'CST6CDT',
      'SamoaStandardTime': 'US/Samoa',
      'HawaiianStandardTime': 'US/Hawaii',
      'AlaskanStandardTime': 'US/Alaska',
      'MexicoStandardTime2': 'MST7MDT',
      'USMountainStandardTime': 'MST7MDT',
      'CanadaCentralStandardTime': 'CST6CDT',
      'MexicoStandardTime': 'CST6CDT',
      'CentralAmericaStandardTime': 'CST6CDT',
      'USEasternStandardTime': 'EST5EDT',
      'SAPacificStandardTime': 'EST5EDT',
      'MalayPeninsulaStandardTime': 'Asia/Kuching',
      'PacificSAStandardTime': 'Canada/Atlantic',
      'AtlanticStandardTime': 'Canada/Atlantic',
      'SAWesternStandardTime': 'Canada/Atlantic',
      'NewfoundlandStandardTime': 'Canada/Newfoundland',
      'AzoresStandardTime': 'Atlantic/Azores',
      'CapeVerdeStandardTime': 'Atlantic/Azores',
      'GMTStandardTime': 'GMT',
      'GreenwichStandardTime': 'GMT',
      'W.CentralAfricaStandardTime': 'Europe/Belgrade',
      'W.EuropeStandardTime': 'Europe/Belgrade',
      'CentralEuropeStandardTime': 'Europe/Belgrade',
      'RomanceStandardTime': 'Europe/Belgrade',
      'CentralEuropeanStandardTime': 'Europe/Belgrade',
      'E.EuropeStandardTime': 'Egypt',
      'SouthAfricaStandardTime': 'Egypt',
      'IsraelStandardTime': 'Egypt',
      'EgyptStandardTime': 'Egypt',
      'NorthAsiaEastStandardTime': 'Asia/Bangkok',
      'SingaporeStandardTime': 'Asia/Bangkok',
      'ChinaStandardTime': 'Asia/Bangkok',
      'W.AustraliaStandardTime': 'Australia/Perth',
      'TaipeiStandardTime': 'Asia/Bangkok',
      'TokyoStandardTime': 'Asia/Tokyo',
      'KoreaStandardTime': 'Asia/Seoul',
      '@tzres.dll,-10': 'Atlantic/Azores',
      '@tzres.dll,-11': 'Atlantic/Azores',
      '@tzres.dll,-12': 'Atlantic/Azores',
      '@tzres.dll,-20': 'Atlantic/Cape_Verde',
      '@tzres.dll,-21': 'Atlantic/Cape_Verde',
      '@tzres.dll,-22': 'Atlantic/Cape_Verde',
      '@tzres.dll,-40': 'Brazil/East',
      '@tzres.dll,-41': 'Brazil/East',
      '@tzres.dll,-42': 'Brazil/East',
      '@tzres.dll,-70': 'Canada/Newfoundland',
      '@tzres.dll,-71': 'Canada/Newfoundland',
      '@tzres.dll,-72': 'Canada/Newfoundland',
      '@tzres.dll,-80': 'Canada/Atlantic',
      '@tzres.dll,-81': 'Canada/Atlantic',
      '@tzres.dll,-82': 'Canada/Atlantic',
      '@tzres.dll,-104': 'America/Cuiaba',
      '@tzres.dll,-105': 'America/Cuiaba',
      '@tzres.dll,-110': 'EST5EDT',
      '@tzres.dll,-111': 'EST5EDT',
      '@tzres.dll,-112': 'EST5EDT',
      '@tzres.dll,-120': 'EST5EDT',
      '@tzres.dll,-121': 'EST5EDT',
      '@tzres.dll,-122': 'EST5EDT',
      '@tzres.dll,-130': 'EST5EDT',
      '@tzres.dll,-131': 'EST5EDT',
      '@tzres.dll,-132': 'EST5EDT',
      '@tzres.dll,-140': 'CST6CDT',
      '@tzres.dll,-141': 'CST6CDT',
      '@tzres.dll,-142': 'CST6CDT',
      '@tzres.dll,-150': 'America/Guatemala',
      '@tzres.dll,-151': 'America/Guatemala',
      '@tzres.dll,-152': 'America/Guatemala',
      '@tzres.dll,-160': 'CST6CDT',
      '@tzres.dll,-161': 'CST6CDT',
      '@tzres.dll,-162': 'CST6CDT',
      '@tzres.dll,-170': 'America/Mexico_City',
      '@tzres.dll,-171': 'America/Mexico_City',
      '@tzres.dll,-172': 'America/Mexico_City',
      '@tzres.dll,-180': 'MST7MDT',
      '@tzres.dll,-181': 'MST7MDT',
      '@tzres.dll,-182': 'MST7MDT',
      '@tzres.dll,-190': 'MST7MDT',
      '@tzres.dll,-191': 'MST7MDT',
      '@tzres.dll,-192': 'MST7MDT',
      '@tzres.dll,-200': 'MST7MDT',
      '@tzres.dll,-201': 'MST7MDT',
      '@tzres.dll,-202': 'MST7MDT',
      '@tzres.dll,-210': 'PST8PDT',
      '@tzres.dll,-211': 'PST8PDT',
      '@tzres.dll,-212': 'PST8PDT',
      '@tzres.dll,-220': 'US/Alaska',
      '@tzres.dll,-221': 'US/Alaska',
      '@tzres.dll,-222': 'US/Alaska',
      '@tzres.dll,-230': 'US/Hawaii',
      '@tzres.dll,-231': 'US/Hawaii',
      '@tzres.dll,-232': 'US/Hawaii',
      '@tzres.dll,-260': 'GMT',
      '@tzres.dll,-261': 'GMT',
      '@tzres.dll,-262': 'GMT',
      '@tzres.dll,-271': 'UTC',
      '@tzres.dll,-272': 'UTC',
      '@tzres.dll,-280': 'Europe/Budapest',
      '@tzres.dll,-281': 'Europe/Budapest',
      '@tzres.dll,-282': 'Europe/Budapest',
      '@tzres.dll,-290': 'Europe/Warsaw',
      '@tzres.dll,-291': 'Europe/Warsaw',
      '@tzres.dll,-292': 'Europe/Warsaw',
      '@tzres.dll,-331': 'Europe/Nicosia',
      '@tzres.dll,-332': 'Europe/Nicosia',
      '@tzres.dll,-340': 'Africa/Cairo',
      '@tzres.dll,-341': 'Africa/Cairo',
      '@tzres.dll,-342': 'Africa/Cairo',
      '@tzres.dll,-350': 'Europe/Sofia',
      '@tzres.dll,-351': 'Europe/Sofia',
      '@tzres.dll,-352': 'Europe/Sofia',
      '@tzres.dll,-365': 'Egypt',
      '@tzres.dll,-390': 'Asia/Kuwait',
      '@tzres.dll,-391': 'Asia/Kuwait',
      '@tzres.dll,-392': 'Asia/Kuwait',
      '@tzres.dll,-400': 'Asia/Baghdad',
      '@tzres.dll,-401': 'Asia/Baghdad',
      '@tzres.dll,-402': 'Asia/Baghdad',
      '@tzres.dll,-410': 'Africa/Nairobi',
      '@tzres.dll,-411': 'Africa/Nairobi',
      '@tzres.dll,-412': 'Africa/Nairobi',
      '@tzres.dll,-434': 'Asia/Tbilisi',
      '@tzres.dll,-435': 'Asia/Tbilisi',
      '@tzres.dll,-440': 'Asia/Muscat',
      '@tzres.dll,-441': 'Asia/Muscat',
      '@tzres.dll,-442': 'Asia/Muscat',
      '@tzres.dll,-447': 'Asia/Baku',
      '@tzres.dll,-448': 'Asia/Baku',
      '@tzres.dll,-449': 'Asia/Baku',
      '@tzres.dll,-450': 'Asia/Yerevan',
      '@tzres.dll,-451': 'Asia/Yerevan',
      '@tzres.dll,-452': 'Asia/Yerevan',
      '@tzres.dll,-460': 'Asia/Kabul',
      '@tzres.dll,-461': 'Asia/Kabul',
      '@tzres.dll,-462': 'Asia/Kabul',
      '@tzres.dll,-471': 'Asia/Yekaterinburg',
      '@tzres.dll,-472': 'Asia/Yekaterinburg',
      '@tzres.dll,-511': 'Asia/Aqtau',
      '@tzres.dll,-512': 'Asia/Aqtau',
      '@tzres.dll,-570': 'Asia/Chongqing',
      '@tzres.dll,-571': 'Asia/Chongqing',
      '@tzres.dll,-572': 'Asia/Chongqing',
      '@tzres.dll,-650': 'Australia/Darwin',
      '@tzres.dll,-651': 'Australia/Darwin',
      '@tzres.dll,-652': 'Australia/Darwin',
      '@tzres.dll,-660': 'Australia/Adelaide',
      '@tzres.dll,-661': 'Australia/Adelaide',
      '@tzres.dll,-662': 'Australia/Adelaide',
      '@tzres.dll,-670': 'Australia/Sydney',
      '@tzres.dll,-671': 'Australia/Sydney',
      '@tzres.dll,-672': 'Australia/Sydney',
      '@tzres.dll,-680': 'Australia/Brisbane',
      '@tzres.dll,-681': 'Australia/Brisbane',
      '@tzres.dll,-682': 'Australia/Brisbane',
      '@tzres.dll,-721': 'Pacific/Port_Moresby',
      '@tzres.dll,-722': 'Pacific/Port_Moresby',
      '@tzres.dll,-731': 'Pacific/Fiji',
      '@tzres.dll,-732': 'Pacific/Fiji',
      '@tzres.dll,-840': 'America/Argentina/Buenos_Aires',
      '@tzres.dll,-841': 'America/Argentina/Buenos_Aires',
      '@tzres.dll,-842': 'America/Argentina/Buenos_Aires',
      '@tzres.dll,-880': 'UTC',
      '@tzres.dll,-930': 'UTC',
      '@tzres.dll,-931': 'UTC',
      '@tzres.dll,-932': 'UTC',
      '@tzres.dll,-1010': 'Asia/Aqtau',
      '@tzres.dll,-1020': 'Asia/Dhaka',
      '@tzres.dll,-1021': 'Asia/Dhaka',
      '@tzres.dll,-1022': 'Asia/Dhaka',
      '@tzres.dll,-1070': 'Asia/Tbilisi',
      '@tzres.dll,-1120': 'America/Cuiaba',
      '@tzres.dll,-1140': 'Pacific/Fiji',
      '@tzres.dll,-1460': 'Pacific/Port_Moresby',
      '@tzres.dll,-1530': 'Asia/Yekaterinburg',
      '@tzres.dll,-1630': 'Europe/Nicosia',
      '@tzres.dll,-1660': 'America/Bahia',
      '@tzres.dll,-1661': 'America/Bahia',
      '@tzres.dll,-1662': 'America/Bahia',
      'Central Standard Time': 'CST6CDT',
      'Pacific Standard Time': 'PST8PDT',
  }

  def ParseKey(self, key):
    """Extract timezone information from the registry."""
    value = key.GetValue('StandardName')
    if value and type(value.data) == unicode:
      # Do a mapping to a value defined as in the Olson database.
      return self.ZONE_LIST.get(value.data.replace(' ', ''), value.data)
