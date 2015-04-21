# -*- coding: utf-8 -*-
"""This file contains preprocessors for Windows."""

import abc
import logging

from dfvfs.helpers import file_system_searcher

from plaso.lib import errors
from plaso.preprocessors import interface
from plaso.preprocessors import manager
from plaso.winreg import cache
from plaso.winreg import path_expander as winreg_path_expander
from plaso.winreg import utils
from plaso.winreg import winregistry


class WindowsRegistryPreprocessPlugin(interface.PreprocessPlugin):
  """Class that defines the Windows Registry preprocess plugin object.

  By default registry needs information about system paths, which excludes
  them to run in priority 1, in some cases they may need to run in priority
  3, for instance if the Registry key is dependent on which version of Windows
  is running, information that is collected during priority 2.
  """
  SUPPORTED_OS = [u'Windows']
  WEIGHT = 2

  REG_KEY = u'\\'
  REG_PATH = u'{sysregistry}'
  REG_FILE = u'SOFTWARE'

  def __init__(self):
    """Initializes the Window Registry preprocess plugin object."""
    super(WindowsRegistryPreprocessPlugin, self).__init__()
    self._file_path_expander = winreg_path_expander.WinRegistryKeyPathExpander()
    self._key_path_expander = None

  def GetValue(self, searcher, knowledge_base):
    """Returns a value gathered from a Registry key for preprocessing.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Raises:
      errors.PreProcessFail: If the preprocessing fails.
    """
    # TODO: optimize this in one find.
    try:
      # TODO: do not pass the full pre_obj here but just the necessary values.
      path = self._file_path_expander.ExpandPath(
          self.REG_PATH, pre_obj=knowledge_base.pre_obj)
    except KeyError:
      path = u''

    if not path:
      raise errors.PreProcessFail(
          u'Unable to expand path: {0:s}'.format(self.REG_PATH))

    find_spec = file_system_searcher.FindSpec(
        location=path, case_sensitive=False)
    path_specs = list(searcher.Find(find_specs=[find_spec]))

    if not path_specs or len(path_specs) != 1:
      raise errors.PreProcessFail(
          u'Unable to find directory: {0:s}'.format(self.REG_PATH))

    directory_location = searcher.GetRelativePath(path_specs[0])
    if not directory_location:
      raise errors.PreProcessFail(
          u'Missing directory location for: {0:s}'.format(self.REG_PATH))

    # The path is split in segments to make it path segement separator
    # independent (and thus platform independent).
    path_segments = searcher.SplitPath(directory_location)
    path_segments.append(self.REG_FILE)

    find_spec = file_system_searcher.FindSpec(
        location=path_segments, case_sensitive=False)
    path_specs = list(searcher.Find(find_specs=[find_spec]))

    if not path_specs:
      raise errors.PreProcessFail(
          u'Unable to find file: {0:s} in directory: {1:s}'.format(
              self.REG_FILE, directory_location))

    if len(path_specs) != 1:
      raise errors.PreProcessFail((
          u'Find for file: {1:s} in directory: {0:s} returned {2:d} '
          u'results.').format(
              self.REG_FILE, directory_location, len(path_specs)))

    file_location = getattr(path_specs[0], u'location', None)
    if not directory_location:
      raise errors.PreProcessFail(
          u'Missing file location for: {0:s} in directory: {1:s}'.format(
              self.REG_FILE, directory_location))

    try:
      file_entry = searcher.GetFileEntryByPathSpec(path_specs[0])
    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to open file entry: {0:s} with error: {1:s}'.format(
              file_location, exception))

    if not file_entry:
      raise errors.PreProcessFail(
          u'Unable to open file entry: {0:s}'.format(file_location))

    # TODO: remove this check win_registry.OpenFile doesn't fail instead?
    try:
      file_object = file_entry.GetFileObject()
    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to open file object: {0:s} with error: {1:s}'.format(
              file_location, exception))
    finally:
      file_object.close()


    win_registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    try:
      winreg_file = win_registry.OpenFile(
          file_entry, codepage=knowledge_base.codepage)
    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to open Registry file: {0:s} with error: {1:s}'.format(
              file_location, exception))

    self.winreg_file = winreg_file

    if not self._key_path_expander:
      # TODO: it is more efficient to have one cache that is passed to every
      # plugin, or maybe one path expander. Or replace the path expander by
      # dfvfs WindowsPathResolver?
      reg_cache = cache.WinRegistryCache()
      reg_cache.BuildCache(winreg_file, self.REG_FILE)
      self._key_path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
          reg_cache=reg_cache)

    try:
      # TODO: do not pass the full pre_obj here but just the necessary values.
      key_path = self._key_path_expander.ExpandPath(
          self.REG_KEY, pre_obj=knowledge_base.pre_obj)
    except KeyError:
      key_path = u''

    if not key_path:
      raise errors.PreProcessFail(
          u'Unable to expand path: {0:s}'.format(self.REG_KEY))

    try:
      key = winreg_file.GetKeyByPath(key_path)
    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to fetch Registry key: {0:s} with error: {1:s}'.format(
              key_path, exception))

    if not key:
      raise errors.PreProcessFail(
          u'Registry key {0:s} does not exist.'.format(self.REG_KEY))

    return self.ParseKey(key)

  @abc.abstractmethod
  def ParseKey(self, key):
    """Extract information from a Registry key and save in storage."""


class WindowsCodepage(WindowsRegistryPreprocessPlugin):
  """A preprocessing class that fetches codepage information."""

  # Defines the preprocess attribute to be set.
  ATTRIBUTE = u'code_page'

  # Depend upon the current control set, thus lower the priority.
  WEIGHT = 3

  REG_KEY = u'{current_control_set}\\Control\\Nls\\CodePage'
  REG_FILE = u'SYSTEM'

  def ParseKey(self, key):
    """Retrieves the codepage or cp1252 by default."""
    value = key.GetValue(u'ACP')
    if value and isinstance(value.data, unicode):
      return u'cp{0:s}'.format(value.data)

    logging.warning(
        u'Unable to determine ASCII string codepage, defaulting to cp1252.')

    return u'cp1252'


class WindowsHostname(WindowsRegistryPreprocessPlugin):
  """A preprocessing class that fetches the hostname information."""

  ATTRIBUTE = u'hostname'

  # Depend upon the current control set to be found.
  WEIGHT = 3

  REG_KEY = u'{current_control_set}\\Control\\ComputerName\\ComputerName'
  REG_FILE = u'SYSTEM'

  def ParseKey(self, key):
    """Extract the hostname from the registry."""
    value = key.GetValue(u'ComputerName')
    if value and isinstance(value.data, unicode):
      return value.data


class WindowsProgramFilesPath(WindowsRegistryPreprocessPlugin):
  """Fetch about the location for the Program Files directory."""

  ATTRIBUTE = u'programfiles'

  REGFILE = u'SOFTWARE'
  REG_KEY = u'\\Microsoft\\Windows\\CurrentVersion'

  def ParseKey(self, key):
    """Extract the version information from the key."""
    value = key.GetValue(u'ProgramFilesDir')
    if value:
      # Remove the first drive letter, eg: "C:\Program Files".
      return u'{0:s}'.format(value.data.partition(u'\\')[2])


class WindowsProgramFilesX86Path(WindowsRegistryPreprocessPlugin):
  """Fetch about the location for the Program Files directory."""

  ATTRIBUTE = u'programfilesx86'

  REGFILE = u'SOFTWARE'
  REG_KEY = u'\\Microsoft\\Windows\\CurrentVersion'

  def ParseKey(self, key):
    """Extract the version information from the key."""
    value = key.GetValue(u'ProgramFilesDir (x86)')
    if value:
      # Remove the first drive letter, eg: "C:\Program Files".
      return u'{0:s}'.format(value.data.partition(u'\\')[2])


class WindowsSystemRegistryPath(interface.PathPreprocessPlugin):
  """Get the system registry path."""
  SUPPORTED_OS = [u'Windows']
  ATTRIBUTE = u'sysregistry'
  PATH = u'/(Windows|WinNT|WINNT35|WTSRV)/System32/config'


class WindowsSystemRootPath(interface.PathPreprocessPlugin):
  """Get the system root path."""
  SUPPORTED_OS = [u'Windows']
  ATTRIBUTE = u'systemroot'
  PATH = u'/(Windows|WinNT|WINNT35|WTSRV)'


class WindowsTimeZone(WindowsRegistryPreprocessPlugin):
  """A preprocessing class that fetches timezone information."""

  # Defines the preprocess attribute to be set.
  ATTRIBUTE = u'time_zone_str'

  # Depend upon the current control set, thus lower the priority.
  WEIGHT = 3

  REG_KEY = u'{current_control_set}\\Control\\TimeZoneInformation'
  REG_FILE = u'SYSTEM'

  # transform gathered from these sources:
  # Prebuilt from:
  # HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Time Zones\
  ZONE_LIST = {
      u'AlaskanStandardTime': u'US/Alaska',
      u'AtlanticStandardTime': u'Canada/Atlantic',
      u'AzoresStandardTime': u'Atlantic/Azores',
      u'CanadaCentralStandardTime': u'CST6CDT',
      u'CapeVerdeStandardTime': u'Atlantic/Azores',
      u'CentralAmericaStandardTime': u'CST6CDT',
      u'CentralDaylightTime': u'CST6CDT',
      u'CentralEuropeanStandardTime': u'Europe/Belgrade',
      u'CentralEuropeStandardTime': u'Europe/Belgrade',
      u'Central Standard Time': u'CST6CDT',
      u'CentralStandardTime': u'CST6CDT',
      u'ChinaStandardTime': u'Asia/Bangkok',
      u'EasternDaylightTime': u'EST5EDT',
      u'EasternStandardTime': u'EST5EDT',
      u'E.EuropeStandardTime': u'Egypt',
      u'EgyptStandardTime': u'Egypt',
      u'GMTStandardTime': u'GMT',
      u'GreenwichStandardTime': u'GMT',
      u'HawaiianStandardTime': u'US/Hawaii',
      u'IndiaStandardTime': u'Asia/Kolkata',
      u'IsraelStandardTime': u'Egypt',
      u'KoreaStandardTime': u'Asia/Seoul',
      u'MalayPeninsulaStandardTime': u'Asia/Kuching',
      u'MexicoStandardTime2': u'MST7MDT',
      u'MexicoStandardTime': u'CST6CDT',
      u'MountainDaylightTime': u'MST7MDT',
      u'MountainStandardTime': u'MST7MDT',
      u'NewfoundlandStandardTime': u'Canada/Newfoundland',
      u'NorthAsiaEastStandardTime': u'Asia/Bangkok',
      u'PacificDaylightTime': u'PST8PDT',
      u'PacificSAStandardTime': u'Canada/Atlantic',
      u'Pacific Standard Time': u'PST8PDT',
      u'PacificStandardTime': u'PST8PDT',
      u'RomanceStandardTime': u'Europe/Belgrade',
      u'SamoaStandardTime': u'US/Samoa',
      u'SAPacificStandardTime': u'EST5EDT',
      u'SAWesternStandardTime': u'Canada/Atlantic',
      u'SingaporeStandardTime': u'Asia/Bangkok',
      u'SouthAfricaStandardTime': u'Egypt',
      u'TaipeiStandardTime': u'Asia/Bangkok',
      u'TokyoStandardTime': u'Asia/Tokyo',
      u'@tzres.dll,-1010': u'Asia/Aqtau',
      u'@tzres.dll,-1020': u'Asia/Dhaka',
      u'@tzres.dll,-1021': u'Asia/Dhaka',
      u'@tzres.dll,-1022': u'Asia/Dhaka',
      u'@tzres.dll,-104': u'America/Cuiaba',
      u'@tzres.dll,-105': u'America/Cuiaba',
      u'@tzres.dll,-1070': u'Asia/Tbilisi',
      u'@tzres.dll,-10': u'Atlantic/Azores',
      u'@tzres.dll,-110': u'EST5EDT',
      u'@tzres.dll,-111': u'EST5EDT',
      u'@tzres.dll,-1120': u'America/Cuiaba',
      u'@tzres.dll,-112': u'EST5EDT',
      u'@tzres.dll,-1140': u'Pacific/Fiji',
      u'@tzres.dll,-11': u'Atlantic/Azores',
      u'@tzres.dll,-120': u'EST5EDT',
      u'@tzres.dll,-121': u'EST5EDT',
      u'@tzres.dll,-122': u'EST5EDT',
      u'@tzres.dll,-12': u'Atlantic/Azores',
      u'@tzres.dll,-130': u'EST5EDT',
      u'@tzres.dll,-131': u'EST5EDT',
      u'@tzres.dll,-132': u'EST5EDT',
      u'@tzres.dll,-140': u'CST6CDT',
      u'@tzres.dll,-141': u'CST6CDT',
      u'@tzres.dll,-142': u'CST6CDT',
      u'@tzres.dll,-1460': u'Pacific/Port_Moresby',
      u'@tzres.dll,-150': u'America/Guatemala',
      u'@tzres.dll,-151': u'America/Guatemala',
      u'@tzres.dll,-152': u'America/Guatemala',
      u'@tzres.dll,-1530': u'Asia/Yekaterinburg',
      u'@tzres.dll,-160': u'CST6CDT',
      u'@tzres.dll,-161': u'CST6CDT',
      u'@tzres.dll,-162': u'CST6CDT',
      u'@tzres.dll,-1630': u'Europe/Nicosia',
      u'@tzres.dll,-1660': u'America/Bahia',
      u'@tzres.dll,-1661': u'America/Bahia',
      u'@tzres.dll,-1662': u'America/Bahia',
      u'@tzres.dll,-170': u'America/Mexico_City',
      u'@tzres.dll,-171': u'America/Mexico_City',
      u'@tzres.dll,-172': u'America/Mexico_City',
      u'@tzres.dll,-180': u'MST7MDT',
      u'@tzres.dll,-181': u'MST7MDT',
      u'@tzres.dll,-182': u'MST7MDT',
      u'@tzres.dll,-190': u'MST7MDT',
      u'@tzres.dll,-191': u'MST7MDT',
      u'@tzres.dll,-192': u'MST7MDT',
      u'@tzres.dll,-200': u'MST7MDT',
      u'@tzres.dll,-201': u'MST7MDT',
      u'@tzres.dll,-202': u'MST7MDT',
      u'@tzres.dll,-20': u'Atlantic/Cape_Verde',
      u'@tzres.dll,-210': u'PST8PDT',
      u'@tzres.dll,-211': u'PST8PDT',
      u'@tzres.dll,-212': u'PST8PDT',
      u'@tzres.dll,-21': u'Atlantic/Cape_Verde',
      u'@tzres.dll,-220': u'US/Alaska',
      u'@tzres.dll,-221': u'US/Alaska',
      u'@tzres.dll,-222': u'US/Alaska',
      u'@tzres.dll,-22': u'Atlantic/Cape_Verde',
      u'@tzres.dll,-230': u'US/Hawaii',
      u'@tzres.dll,-231': u'US/Hawaii',
      u'@tzres.dll,-232': u'US/Hawaii',
      u'@tzres.dll,-260': u'GMT',
      u'@tzres.dll,-261': u'GMT',
      u'@tzres.dll,-262': u'GMT',
      u'@tzres.dll,-271': u'UTC',
      u'@tzres.dll,-272': u'UTC',
      u'@tzres.dll,-280': u'Europe/Budapest',
      u'@tzres.dll,-281': u'Europe/Budapest',
      u'@tzres.dll,-282': u'Europe/Budapest',
      u'@tzres.dll,-290': u'Europe/Warsaw',
      u'@tzres.dll,-291': u'Europe/Warsaw',
      u'@tzres.dll,-292': u'Europe/Warsaw',
      u'@tzres.dll,-331': u'Europe/Nicosia',
      u'@tzres.dll,-332': u'Europe/Nicosia',
      u'@tzres.dll,-340': u'Africa/Cairo',
      u'@tzres.dll,-341': u'Africa/Cairo',
      u'@tzres.dll,-342': u'Africa/Cairo',
      u'@tzres.dll,-350': u'Europe/Sofia',
      u'@tzres.dll,-351': u'Europe/Sofia',
      u'@tzres.dll,-352': u'Europe/Sofia',
      u'@tzres.dll,-365': u'Egypt',
      u'@tzres.dll,-390': u'Asia/Kuwait',
      u'@tzres.dll,-391': u'Asia/Kuwait',
      u'@tzres.dll,-392': u'Asia/Kuwait',
      u'@tzres.dll,-400': u'Asia/Baghdad',
      u'@tzres.dll,-401': u'Asia/Baghdad',
      u'@tzres.dll,-402': u'Asia/Baghdad',
      u'@tzres.dll,-40': u'Brazil/East',
      u'@tzres.dll,-410': u'Africa/Nairobi',
      u'@tzres.dll,-411': u'Africa/Nairobi',
      u'@tzres.dll,-412': u'Africa/Nairobi',
      u'@tzres.dll,-41': u'Brazil/East',
      u'@tzres.dll,-42': u'Brazil/East',
      u'@tzres.dll,-434': u'Asia/Tbilisi',
      u'@tzres.dll,-435': u'Asia/Tbilisi',
      u'@tzres.dll,-440': u'Asia/Muscat',
      u'@tzres.dll,-441': u'Asia/Muscat',
      u'@tzres.dll,-442': u'Asia/Muscat',
      u'@tzres.dll,-447': u'Asia/Baku',
      u'@tzres.dll,-448': u'Asia/Baku',
      u'@tzres.dll,-449': u'Asia/Baku',
      u'@tzres.dll,-450': u'Asia/Yerevan',
      u'@tzres.dll,-451': u'Asia/Yerevan',
      u'@tzres.dll,-452': u'Asia/Yerevan',
      u'@tzres.dll,-460': u'Asia/Kabul',
      u'@tzres.dll,-461': u'Asia/Kabul',
      u'@tzres.dll,-462': u'Asia/Kabul',
      u'@tzres.dll,-471': u'Asia/Yekaterinburg',
      u'@tzres.dll,-472': u'Asia/Yekaterinburg',
      u'@tzres.dll,-480': u'Asia/Karachi',
      u'@tzres.dll,-481': u'Asia/Karachi',
      u'@tzres.dll,-482': u'Asia/Karachi',
      u'@tzres.dll,-490': u'Asia/Kolkata',
      u'@tzres.dll,-491': u'Asia/Kolkata',
      u'@tzres.dll,-492': u'Asia/Kolkata',
      u'@tzres.dll,-500': u'Asia/Kathmandu',
      u'@tzres.dll,-501': u'Asia/Kathmandu',
      u'@tzres.dll,-502': u'Asia/Kathmandu',
      u'@tzres.dll,-510': u'Asia/Dhaka',
      u'@tzres.dll,-511': u'Asia/Aqtau',
      u'@tzres.dll,-512': u'Asia/Aqtau',
      u'@tzres.dll,-570': u'Asia/Chongqing',
      u'@tzres.dll,-571': u'Asia/Chongqing',
      u'@tzres.dll,-572': u'Asia/Chongqing',
      u'@tzres.dll,-650': u'Australia/Darwin',
      u'@tzres.dll,-651': u'Australia/Darwin',
      u'@tzres.dll,-652': u'Australia/Darwin',
      u'@tzres.dll,-660': u'Australia/Adelaide',
      u'@tzres.dll,-661': u'Australia/Adelaide',
      u'@tzres.dll,-662': u'Australia/Adelaide',
      u'@tzres.dll,-670': u'Australia/Sydney',
      u'@tzres.dll,-671': u'Australia/Sydney',
      u'@tzres.dll,-672': u'Australia/Sydney',
      u'@tzres.dll,-680': u'Australia/Brisbane',
      u'@tzres.dll,-681': u'Australia/Brisbane',
      u'@tzres.dll,-682': u'Australia/Brisbane',
      u'@tzres.dll,-70': u'Canada/Newfoundland',
      u'@tzres.dll,-71': u'Canada/Newfoundland',
      u'@tzres.dll,-721': u'Pacific/Port_Moresby',
      u'@tzres.dll,-722': u'Pacific/Port_Moresby',
      u'@tzres.dll,-72': u'Canada/Newfoundland',
      u'@tzres.dll,-731': u'Pacific/Fiji',
      u'@tzres.dll,-732': u'Pacific/Fiji',
      u'@tzres.dll,-80': u'Canada/Atlantic',
      u'@tzres.dll,-81': u'Canada/Atlantic',
      u'@tzres.dll,-82': u'Canada/Atlantic',
      u'@tzres.dll,-840': u'America/Argentina/Buenos_Aires',
      u'@tzres.dll,-841': u'America/Argentina/Buenos_Aires',
      u'@tzres.dll,-842': u'America/Argentina/Buenos_Aires',
      u'@tzres.dll,-880': u'UTC',
      u'@tzres.dll,-930': u'UTC',
      u'@tzres.dll,-931': u'UTC',
      u'@tzres.dll,-932': u'UTC',
      u'USEasternStandardTime': u'EST5EDT',
      u'USMountainStandardTime': u'MST7MDT',
      u'W.AustraliaStandardTime': u'Australia/Perth',
      u'W.CentralAfricaStandardTime': u'Europe/Belgrade',
      u'W.EuropeStandardTime': u'Europe/Belgrade',
  }

  def ParseKey(self, key):
    """Extract timezone information from the registry."""
    value = key.GetValue(u'StandardName')
    if value and isinstance(value.data, unicode):
      # Do a mapping to a value defined as in the Olson database.
      return self.ZONE_LIST.get(value.data.replace(u' ', u''), value.data)


class WindowsUsers(WindowsRegistryPreprocessPlugin):
  """Fetch information about user profiles."""

  ATTRIBUTE = u'users'

  REG_FILE = u'SOFTWARE'
  REG_KEY = u'\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList'

  def ParseKey(self, key):
    """Extract current control set information."""
    users = []

    for sid in key.GetSubkeys():
      # TODO: as part of artifacts, create a proper object for this.
      user = {}
      user[u'sid'] = sid.name
      value = sid.GetValue(u'ProfileImagePath')
      if value:
        user[u'path'] = value.data
        user[u'name'] = utils.WinRegBasename(user[u'path'])

      users.append(user)

    return users


class WindowsVersion(WindowsRegistryPreprocessPlugin):
  """Fetch information about the current Windows version."""

  ATTRIBUTE = u'osversion'

  REGFILE = u'SOFTWARE'
  REG_KEY = u'\\Microsoft\\Windows NT\\CurrentVersion'

  def ParseKey(self, key):
    """Extract the version information from the key."""
    value = key.GetValue(u'ProductName')
    if value:
      return u'{0:s}'.format(value.data)


class WindowsWinDirPath(interface.PathPreprocessPlugin):
  """Get the system path."""
  SUPPORTED_OS = [u'Windows']
  ATTRIBUTE = u'windir'
  PATH = u'/(Windows|WinNT|WINNT35|WTSRV)'


manager.PreprocessPluginsManager.RegisterPlugins([
    WindowsCodepage, WindowsHostname, WindowsProgramFilesPath,
    WindowsProgramFilesX86Path, WindowsSystemRegistryPath,
    WindowsSystemRootPath, WindowsTimeZone, WindowsUsers, WindowsVersion,
    WindowsWinDirPath])
