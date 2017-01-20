# -*- coding: utf-8 -*-
"""This file contains preprocessors for Windows."""

import logging

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.preprocessors import interface
from plaso.preprocessors import manager
from plaso.winnt import time_zones


class WindowsCodepagePreprocessPlugin(
    interface.WindowsRegistryValuePreprocessPlugin):
  """The Windows codepage preprocess plugin."""

  _REGISTRY_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Nls\\CodePage')
  _REGISTRY_VALUE_NAME = u'ACP'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the value data is not a string type.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Registry key: {0:s}, value: {1:s} type: {2:s}.'.format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME,
              type(value_data)))

    # Map the Windows code page name to a Python equivalent name.
    codepage = u'cp{0:s}'.format(value_data)

    try:
      knowledge_base.SetCodepage(codepage)
    except ValueError:
      # TODO: add and store preprocessing errors.
      pass


class WindowsHostnamePreprocessPlugin(
    interface.WindowsRegistryValuePreprocessPlugin):
  """The Windows hostname preprocess plugin."""

  _REGISTRY_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ComputerName\\'
      u'ComputerName')
  _REGISTRY_VALUE_NAME = u'ComputerName'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the value data is not a string type.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Registry key: {0:s}, value: {1:s} type: {2:s}.'.format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME,
              type(value_data)))

    hostname_artifact = artifacts.HostnameArtifact(name=value_data)
    knowledge_base.SetHostname(hostname_artifact)


class WindowsProgramFilesEnvironmentVariable(
    interface.WindowsRegistryEnvironmentVariable):
  """The Windows %ProgramFiles% environment variable preprocess plugin."""

  _NAME = u'programfiles'
  _REGISTRY_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion')
  _REGISTRY_VALUE_NAME = u'ProgramFilesDir'


class WindowsProgramFilesX86EnvironmentVariable(
    interface.WindowsRegistryEnvironmentVariable):
  """The Windows %ProgramFilesX86% environment variable preprocess plugin."""

  _NAME = u'programfilesx86'
  _REGISTRY_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion')
  _REGISTRY_VALUE_NAME = u'ProgramFilesDir (x86)'


class WindowsSystemProductPlugin(
    interface.WindowsRegistryValuePreprocessPlugin):
  """The Windows system product information preprocess plugin."""

  _REGISTRY_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
  _REGISTRY_VALUE_NAME = u'ProductName'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the value data is not a string type.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Registry key: {0:s}, value: {1:s} type: {2:s}.'.format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME,
              type(value_data)))

    knowledge_base.SetValue(u'operating_system_product', value_data)


class WindowsSystemRootEnvironmentVariable(
    interface.WindowsPathEnvironmentVariablePlugin):
  """The Windows %SystemRoot% environment variable preprocess plugin."""

  _NAME = u'systemroot'
  _PATH_REGEX = u'/(Windows|WinNT|WINNT35|WTSRV)'


class WindowsSystemVersionPlugin(
    interface.WindowsRegistryValuePreprocessPlugin):
  """The Windows system version information preprocess plugin."""

  _REGISTRY_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
  _REGISTRY_VALUE_NAME = u'CurrentVersion'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the value data is not a string type.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Registry key: {0:s}, value: {1:s} type: {2:s}.'.format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME,
              type(value_data)))

    knowledge_base.SetValue(u'operating_system_version', value_data)


class WindowsTimeZonePreprocessPlugin(
    interface.WindowsRegistryValuePreprocessPlugin):
  """The Windows time zone preprocess plugin."""

  _REGISTRY_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
      u'TimeZoneInformation')
  _REGISTRY_VALUE_NAME = u'StandardName'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the value data is not a string type.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Registry key: {0:s}, value: {1:s} type: {2:s}.'.format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME,
              type(value_data)))

    # Map the Windows time zone name to a Python equivalent name.
    lookup_key = value_data.replace(u' ', u'')

    time_zone = time_zones.TIME_ZONES.get(lookup_key, value_data)
    if not time_zone:
      return

    try:
      # Catch and warn about unsupported mapping.
      knowledge_base.SetTimeZone(time_zone)
    except ValueError:
      # TODO: add and store preprocessing errors.
      time_zone = value_data
      logging.warning(
          u'Unable to map: "{0:s}" to time zone'.format(value_data))


class WindowsUserAccountsPreprocessPlugin(
    interface.WindowsRegistryKeyPreprocessPlugin):
  """The Windows user accounts preprocess plugin."""

  _REGISTRY_KEY_PATH = (
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

  def _ParseKey(self, knowledge_base, registry_key):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      registry_key (WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      if not subkey.name:
        # TODO: add and store preprocessing errors.
        continue

      user_account = artifacts.UserAccountArtifact(
          identifier=subkey.name)

      registry_value = subkey.GetValueByName(u'ProfileImagePath')
      if registry_value:
        profile_path = registry_value.GetDataAsObject()
        username = self._GetUsernameFromPath(profile_path)

        user_account.user_directory = profile_path or None
        user_account.username = username or None

      try:
        knowledge_base.AddUserAccount(user_account)
      except KeyError:
        # TODO: add and store preprocessing errors.
        pass


class WindowsWinDirEnvironmentVariable(
    interface.WindowsPathEnvironmentVariablePlugin):
  """The Windows %WinDir% environment variable preprocess plugin."""

  _NAME = u'windir'
  _PATH_REGEX = u'/(Windows|WinNT|WINNT35|WTSRV)'


manager.PreprocessPluginsManager.RegisterPlugins([
    WindowsCodepagePreprocessPlugin, WindowsHostnamePreprocessPlugin,
    WindowsProgramFilesEnvironmentVariable,
    WindowsProgramFilesX86EnvironmentVariable, WindowsSystemProductPlugin,
    WindowsSystemRootEnvironmentVariable, WindowsSystemVersionPlugin,
    WindowsTimeZonePreprocessPlugin, WindowsUserAccountsPreprocessPlugin,
    WindowsWinDirEnvironmentVariable])
