# -*- coding: utf-8 -*-
"""This file contains preprocessors for Windows."""

import abc
import logging

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.preprocessors import interface
from plaso.preprocessors import manager
from plaso.winnt import time_zones


class WindowsPathPreprocessPlugin(interface.PreprocessPlugin):
  """Returns a Windows path."""

  WEIGHT = 1

  def GetValue(self, searcher, unused_knowledge_base):
    """Searches a path on a file system for a preprocessing attribute.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Returns:
      str: first path location string that is found.

    Raises:
      PreProcessFail: if the path could not be found.
    """
    path_specs = self._FindPathSpecs(searcher, self.PATH)
    if not path_specs:
      raise errors.PreProcessFail(
          u'Unable to find path: {0:s}'.format(self.PATH))

    relative_path = searcher.GetRelativePath(path_specs[0])
    if not relative_path:
      raise errors.PreProcessFail(
          u'Missing relative path for: {0:s}'.format(self.PATH))

    if relative_path.startswith(u'/'):
      relative_path = u'\\'.join(relative_path.split(u'/'))
    return relative_path


class WindowsPathEnvironmentVariablePlugin(WindowsPathPreprocessPlugin):
  """Plugin to determine the value of an environment variable."""

  def GetValue(self, searcher, knowledge_base):
    """Searches a path on a file system for a preprocessing attribute.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Returns:
      EnvironmentVariableArtifact: environment variable artifact or None.
    """
    relative_path = super(WindowsPathEnvironmentVariablePlugin, self).GetValue(
        searcher, knowledge_base)
    return artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self.ATTRIBUTE, value=relative_path)


class WindowsSystemRegistryPath(WindowsPathPreprocessPlugin):
  """Get the system registry path."""

  SUPPORTED_OS = [u'Windows']
  ATTRIBUTE = u'sysregistry'
  PATH = u'/(Windows|WinNT|WINNT35|WTSRV)/System32/config'


class WindowsRegistryPreprocessPlugin(interface.PreprocessPlugin):
  """Class that defines the Windows Registry preprocess plugin object.

  By default registry needs information about system paths, which excludes
  them to run in priority 1, in some cases they may need to run in priority
  3, for instance if the Registry key is dependent on which version of Windows
  is running, information that is collected during priority 2.
  """
  SUPPORTED_OS = [u'Windows']
  WEIGHT = 2

  KEY_PATH = u''

  @abc.abstractmethod
  def _ParseKey(self, registry_key):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.

    Returns:
      object: preprocess attribute value or None.
    """

  # TODO: remove after refactor interface.
  def GetValue(self, searcher, knowledge_base):
    pass

  def Run(self, win_registry, knowledge_base):
    """Runs the plugins to determine the value of a preprocessing attribute.

    Args:
      win_registry (WinRegistry): Windows Registry.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Raises:
      PreProcessFail: If a preprocessing failed.
    """
    try:
      registry_key = win_registry.GetKeyByPath(self.KEY_PATH)

    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to retrieve Registry key: {0:s} with error: {1:s}'.format(
              self.KEY_PATH, exception))

    if not registry_key:
      return

    attribute_value = self._ParseKey(registry_key)
    if not attribute_value:
      return

    self._SetAttributeValue(attribute_value, knowledge_base)


class WindowsUsers(WindowsRegistryPreprocessPlugin):
  """Fetch information about user profiles."""

  ATTRIBUTE = u'users'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion\\'
      u'ProfileList')

  def _GetUsernameFromPath(self, path):
    """Retrieves the username from a Windows profile path.

    Trailing path path segment are igored.

    Args:
      path (str): a Windows path with '\\' as path segment separator.

    Returns:
      str: basename which is the last path segment.
    """
    # Strip trailing key separators.
    while path and path[-1] == u'\\':
      path = path[:-1]

    if path:
      _, _, path = path.rpartition(u'\\')
    return path

  def _ParseKey(self, registry_key):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.

    Returns:
      list[UserAccountArtifact]: user account artifacts.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    users = []
    for subkey in registry_key.GetSubkeys():
      if not subkey.name:
        # TODO: add and store preprocessing errors.
        continue

      user_account_artifact = artifacts.UserAccountArtifact(
          identifier=subkey.name)

      registry_value = subkey.GetValueByName(u'ProfileImagePath')
      if registry_value:
        profile_path = registry_value.GetDataAsObject()
        username = self._GetUsernameFromPath(profile_path)

        user_account_artifact.user_directory = profile_path or None
        user_account_artifact.username = username or None

      users.append(user_account_artifact)

    if not users:
      raise errors.PreProcessFail(u'Unable to find any users on the system.')
    return users


class WindowsRegistryValuePreprocessPlugin(WindowsRegistryPreprocessPlugin):
  """Class that defines a Windows Registry value preprocessing plugin."""

  DEFAULT_ATTRIBUTE_VALUE = None
  VALUE_NAME = u''

  def _ParseKey(self, registry_key):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.

    Returns:
      object: preprocess attribute value or None.
    """
    if not registry_key:
      logging.warning(
          u'Registry key: {0:s} does not exist'.format(self.KEY_PATH))
      return self.DEFAULT_ATTRIBUTE_VALUE

    registry_value = registry_key.GetValueByName(self.VALUE_NAME)
    if not registry_value:
      logging.warning(
          u'Registry value: {0:s} does not exist'.format(self.VALUE_NAME))
      return self.DEFAULT_ATTRIBUTE_VALUE

    return self._ParseValue(registry_value)

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for a preprocessing attribute.

    Args:
      registry_value (WinRegistryValue): Windows Registry value.

    Returns:
      object: preprocess attribute value or None.
    """
    return registry_value.GetDataAsObject()


class WindowsCodepage(WindowsRegistryValuePreprocessPlugin):
  """Windows preprocess plugin to determine the codepage."""

  ATTRIBUTE = u'code_page'
  DEFAULT_ATTRIBUTE_VALUE = u'cp1252'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Nls\\CodePage')
  VALUE_NAME = u'ACP'

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for a preprocessing attribute.

    Args:
      registry_value (WinRegistryValue): Windows Registry value.

    Returns:
      object: preprocess attribute value or None.
    """
    value_data = registry_value.GetDataAsObject()
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      logging.warning(
          u'Unsupported Registry value: {0:s} data type'.format(
              self.VALUE_NAME))
      return self.DEFAULT_ATTRIBUTE_VALUE

    # Map the Windows code page name to a Python equivalent name.
    # TODO: add a value sanity check.
    return u'cp{0:s}'.format(value_data)


class WindowsSystemProductPlugin(WindowsRegistryValuePreprocessPlugin):
  """Plugin to determine Windows system product information."""

  ATTRIBUTE = u'operating_system_product'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
  VALUE_NAME = u'ProductName'


class WindowsSystemRootEnvironmentVariable(
    WindowsPathEnvironmentVariablePlugin):
  """Plugin to determine the value of the %SystemRoot% environment variable."""

  SUPPORTED_OS = [u'Windows']
  ATTRIBUTE = u'systemroot'
  PATH = u'/(Windows|WinNT|WINNT35|WTSRV)'


class WindowsSystemVersionPlugin(WindowsRegistryValuePreprocessPlugin):
  """Plugin to determine Windows system version information."""

  ATTRIBUTE = u'operating_system_version'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
  VALUE_NAME = u'CurrentVersion'


class WindowsTimeZone(WindowsRegistryValuePreprocessPlugin):
  """A preprocessing class that fetches timezone information."""

  ATTRIBUTE = u'time_zone_str'
  DEFAULT_ATTRIBUTE_VALUE = u'UTC'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
      u'TimeZoneInformation')
  VALUE_NAME = u'StandardName'

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for a preprocessing attribute.

    Args:
      registry_value (WinRegistryValue): Windows Registry value.

    Returns:
      object: preprocess attribute value or None.
    """
    value_data = registry_value.GetDataAsObject()
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      logging.warning(
          u'Unsupported Registry value: {0:s} data type'.format(
              self.VALUE_NAME))
      return self.DEFAULT_ATTRIBUTE_VALUE

    # Map the Windows time zone name to a Python equivalent name.
    lookup_key = value_data.replace(u' ', u'')
    return time_zones.TIME_ZONES.get(lookup_key, value_data)


class WindowsRegistryEnvironmentVariable(WindowsRegistryValuePreprocessPlugin):
  """Preprocess plugin to determine the value of an environment variable."""

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for a preprocessing attribute.

    Args:
      registry_value (WinRegistryValue): Windows Registry value.

    Returns:
      EnvironmentVariableArtifact: environment variable artifact or None.
    """
    value_data = registry_value.GetDataAsObject()
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      logging.warning(
          u'Unsupported Registry value: {0:s} data type'.format(
              self.VALUE_NAME))
      return self.DEFAULT_ATTRIBUTE_VALUE

    # Here we remove the drive letter, e.g. "C:\Program Files".
    _, _, path = value_data.rpartition(u':')
    return artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self.ATTRIBUTE, value=path)


class WindowsWinDirEnvironmentVariable(WindowsPathEnvironmentVariablePlugin):
  """Plugin to determine the value of the %WinDir% environment variable."""

  SUPPORTED_OS = [u'Windows']
  ATTRIBUTE = u'windir'
  PATH = u'/(Windows|WinNT|WINNT35|WTSRV)'


class WindowsProgramFilesEnvironmentVariable(
    WindowsRegistryEnvironmentVariable):
  """Preprocess plugin to determine the value of %ProgramFiles%."""

  ATTRIBUTE = u'programfiles'
  KEY_PATH = u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion'
  VALUE_NAME = u'ProgramFilesDir'


class WindowsProgramFilesX86EnvironmentVariable(
    WindowsRegistryEnvironmentVariable):
  """Preprocess plugin to determine the value of %ProgramFilesX86%."""

  ATTRIBUTE = u'programfilesx86'
  KEY_PATH = u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion'
  VALUE_NAME = u'ProgramFilesDir (x86)'


class WindowsHostname(WindowsRegistryValuePreprocessPlugin):
  """Windows preprocess plugin to determine the hostname."""

  ATTRIBUTE = u'hostname'
  DEFAULT_ATTRIBUTE_VALUE = u'HOSTNAME'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ComputerName\\'
      u'ComputerName')
  VALUE_NAME = u'ComputerName'

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for a preprocessing attribute.

    Args:
      registry_value (WinRegistryValue): Windows Registry value.

    Returns:
      HostnameArtifact: hostname artifact or None.
    """
    name = registry_value.GetDataAsObject()
    if name:
      return artifacts.HostnameArtifact(name=name)


manager.PreprocessPluginsManager.RegisterPlugins([
    WindowsCodepage, WindowsHostname, WindowsProgramFilesEnvironmentVariable,
    WindowsProgramFilesX86EnvironmentVariable, WindowsSystemRegistryPath,
    WindowsSystemProductPlugin, WindowsSystemRootEnvironmentVariable,
    WindowsSystemVersionPlugin, WindowsTimeZone, WindowsUsers,
    WindowsWinDirEnvironmentVariable])
