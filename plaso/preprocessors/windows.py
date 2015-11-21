# -*- coding: utf-8 -*-
"""This file contains preprocessors for Windows."""

import abc
import logging

from plaso.lib import errors
from plaso.lib import py2to3
from plaso.preprocessors import interface
from plaso.preprocessors import manager
from plaso.winnt import time_zones


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


class WindowsWinDirPath(interface.PathPreprocessPlugin):
  """Get the system path."""
  SUPPORTED_OS = [u'Windows']
  ATTRIBUTE = u'windir'
  PATH = u'/(Windows|WinNT|WINNT35|WTSRV)'


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
    """Parses a Windows Registry key for the preprocessing attribute.

    Args:
      registry_key: The Registry key (instance of WinRegistryKey).

    Returns:
      The preprocessing attribute value or None.
    """

  # TODO: remove after refactor interface.
  def GetValue(self, searcher, knowledge_base):
    pass

  def Run(self, win_registry, knowledge_base):
    """Runs the plugins to determine the value of the preprocessing attribute.

    The resulting preprocessing attribute value is stored in the knowledge base.

    Args:
      win_registry: The Windows Registry object (instance of WinRegistry).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Raises:
      PreProcessFail: If the preprocessing failed.
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

    knowledge_base.SetValue(self.ATTRIBUTE, attribute_value)

    # TODO: remove.
    attribute_value = knowledge_base.GetValue(
        self.ATTRIBUTE, default_value=u'N/A')
    logging.info(u'[PreProcess] Set attribute: {0:s} to {1:s}'.format(
        self.ATTRIBUTE, attribute_value))


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
      path: a Windows path with \\ as the path segment separator.

    Returns:
      The basename (or last path segment).
    """
    # Strip trailing key separators.
    while path and path[-1] == u'\\':
      path = path[:-1]

    if path:
      _, _, path = path.rpartition(u'\\')
    return path

  def _ParseKey(self, registry_key):
    """Parses a Windows Registry key for the preprocessing attribute.

    Args:
      registry_key: The Registry key (instance of WinRegistryKey).

    Returns:
      The preprocessing attribute value or None.
    """
    users = []
    for subkey in registry_key.GetSubkeys():
      # TODO: create a proper object for this.
      user = {}
      user[u'sid'] = subkey.name
      value = subkey.GetValueByName(u'ProfileImagePath')
      if value:
        user[u'path'] = value.data
        user[u'name'] = self._GetUsernameFromPath(user[u'path'])

      users.append(user)

    return users


class WindowsRegistryValuePreprocessPlugin(WindowsRegistryPreprocessPlugin):
  """Class that defines a Windows Registry value preprocessing plugin."""

  DEFAULT_ATTRIBUTE_VALUE = None
  VALUE_NAME = u''

  def _ParseKey(self, registry_key):
    """Parses a Windows Registry key for the preprocessing attribute.

    Args:
      registry_key: The Registry key (instance of WinRegistryKey).

    Returns:
      The preprocessing attribute value or None.
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
    """Parses a Windows Registry value for the preprocessing attribute.

    Args:
      registry_value: The Registry value (instance of WinRegistryValue).

    Returns:
      The preprocessing attribute value or None.
    """
    return registry_value.data


class WindowsCodepage(WindowsRegistryValuePreprocessPlugin):
  """Windows preprocess plugin to determine the codepage."""

  ATTRIBUTE = u'code_page'
  DEFAULT_ATTRIBUTE_VALUE = u'cp1252'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Nls\\CodePage')
  VALUE_NAME = u'ACP'

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for the preprocessing attribute.

    Args:
      registry_value: The Registry value (instance of WinRegistryValue).

    Returns:
      The preprocessing attribute value or None.
    """
    value_data = registry_value.data
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      logging.warning(
          u'Unsupported Registry value: {0:s} data type'.format(
              self.VALUE_NAME))
      return self.DEFAULT_ATTRIBUTE_VALUE

    # Map the Windows code page name to a Python equivalent name.
    # TODO: add a value sanity check.
    return u'cp{0:s}'.format(value_data)


class WindowsHostname(WindowsRegistryValuePreprocessPlugin):
  """Windows preprocess plugin to determine the hostname."""

  ATTRIBUTE = u'hostname'
  DEFAULT_ATTRIBUTE_VALUE = u'HOSTNAME'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ComputerName\\'
      u'ComputerName')
  VALUE_NAME = u'ComputerName'


class WindowsTimeZone(WindowsRegistryValuePreprocessPlugin):
  """A preprocessing class that fetches timezone information."""

  ATTRIBUTE = u'time_zone_str'
  DEFAULT_ATTRIBUTE_VALUE = u'UTC'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
      u'TimeZoneInformation')
  VALUE_NAME = u'StandardName'

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for the preprocessing attribute.

    Args:
      registry_value: The Registry value (instance of WinRegistryValue).

    Returns:
      The preprocessing attribute value or None.
    """
    value_data = registry_value.data
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      logging.warning(
          u'Unsupported Registry value: {0:s} data type'.format(
              self.VALUE_NAME))
      return self.DEFAULT_ATTRIBUTE_VALUE

    # Map the Windows time zone name to a Python equivalent name.
    lookup_key = value_data.replace(u' ', u'')
    return time_zones.TIME_ZONES.get(lookup_key, value_data)


class WindowsVersion(WindowsRegistryValuePreprocessPlugin):
  """Fetch information about the current Windows version."""

  ATTRIBUTE = u'osversion'
  KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion')
  VALUE_NAME = u'ProductName'


class WindowsRegistryPathEnvironmentValue(WindowsRegistryValuePreprocessPlugin):
  """Windows preprocess plugin to determine a path environment variable."""

  def _ParseValue(self, registry_value):
    """Parses a Windows Registry value for the preprocessing attribute.

    Args:
      registry_value: The Registry value (instance of WinRegistryValue).

    Returns:
      The preprocessing attribute value or None.
    """
    value_data = registry_value.data
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      logging.warning(
          u'Unsupported Registry value: {0:s} data type'.format(
              self.VALUE_NAME))
      return self.DEFAULT_ATTRIBUTE_VALUE

    # Here we remove the drive letter, e.g. "C:\Program Files".
    _, _, path = value_data.rpartition(u':')
    return path


class WindowsProgramFilesPath(WindowsRegistryPathEnvironmentValue):
  """Windows preprocess plugin to determine the location of Program Files."""

  ATTRIBUTE = u'programfiles'
  KEY_PATH = u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion'
  VALUE_NAME = u'ProgramFilesDir'


class WindowsProgramFilesX86Path(WindowsRegistryPathEnvironmentValue):
  """Windows preprocess plugin to determine the location of Program Files."""

  ATTRIBUTE = u'programfilesx86'
  KEY_PATH = u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion'
  VALUE_NAME = u'ProgramFilesDir (x86)'


manager.PreprocessPluginsManager.RegisterPlugins([
    WindowsCodepage, WindowsHostname, WindowsProgramFilesPath,
    WindowsProgramFilesX86Path, WindowsSystemRegistryPath,
    WindowsSystemRootPath, WindowsTimeZone, WindowsUsers, WindowsVersion,
    WindowsWinDirPath])
