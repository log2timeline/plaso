# -*- coding: utf-8 -*-
"""This file contains preprocessors for Windows."""

import logging

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.preprocessors import interface
from plaso.preprocessors import manager
from plaso.winnt import time_zones


class WindowsEnvironmentVariableArtifactPreprocessorPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """Windows environment variable artifact preprocessor plugin interface."""

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Windows Registry value type: {0:s} for '
          u'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    result = False
    evironment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=value_data)

    try:
      knowledge_base.AddEnvironmentVariable(evironment_variable)
      result = True
    except KeyError:
      # TODO: add and store preprocessing errors.
      pass

    return result


class WindowsPathEnvironmentVariableArtifactPreprocessorPlugin(
    interface.FileSystemArtifactPreprocessorPlugin):
  """Windows path environment variable plugin interface."""

  _NAME = None

  def _ParsePathSpecification(
      self, knowledge_base, searcher, file_system, path_specification,
      path_separator):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      path_specification (dfvfs.PathSpec): path specification that contains
          the artifact value data.
      path_separator (str): path segment separator.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    result = False

    relative_path = searcher.GetRelativePath(path_specification)
    if not relative_path:
      raise errors.PreProcessFail(
          u'Unable to read: {0:s} with error: missing relative path'.format(
              self.ARTIFACT_DEFINITION_NAME))

    if path_separator != file_system.PATH_SEPARATOR:
      relative_path_segments = file_system.SplitPath(relative_path)
      relative_path = u'{0:s}{1:s}'.format(
          path_separator, path_separator.join(relative_path_segments))

    evironment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=relative_path)

    try:
      knowledge_base.AddEnvironmentVariable(evironment_variable)
      result = True
    except KeyError:
      # TODO: add and store preprocessing errors.
      pass

    return result


class WindowsCodepagePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows codepage plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsCodePage'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Windows Registry value type: {0:s} for '
          u'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    result = False
    # Map the Windows code page name to a Python equivalent name.
    codepage = u'cp{0:s}'.format(value_data)

    try:
      knowledge_base.SetCodepage(codepage)
      result = True
    except ValueError:
      # TODO: add and store preprocessing errors.
      pass

    return result


class WindowsHostnamePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows hostname plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsComputerName'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Windows Registry value type: {0:s} for '
          u'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    hostname_artifact = artifacts.HostnameArtifact(name=value_data)
    knowledge_base.SetHostname(hostname_artifact)
    return True


class WindowsProgramFilesEnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramFiles% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsEnvironmentVariableProgramFiles'

  _NAME = u'programfiles'


class WindowsProgramFilesX86EnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramFilesX86% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsEnvironmentVariableProgramFilesX86'

  _NAME = u'programfilesx86'


class WindowsSystemProductPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows system product information plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsProductName'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Windows Registry value type: {0:s} for '
          u'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    knowledge_base.SetValue(u'operating_system_product', value_data)
    return True


class WindowsSystemRootEnvironmentVariablePlugin(
    WindowsPathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %SystemRoot% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsEnvironmentVariableSystemRoot'

  _NAME = u'systemroot'


class WindowsSystemVersionPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows system verion information plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsCurrentVersion'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Windows Registry value type: {0:s} for '
          u'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    knowledge_base.SetValue(u'operating_system_version', value_data)
    return True


class WindowsTimeZonePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows time zone plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsTimezone'

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Windows Registry value type: {0:s} for '
          u'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    result = False
    # Map the Windows time zone name to a Python equivalent name.
    lookup_key = value_data.replace(u' ', u'')

    time_zone = time_zones.TIME_ZONES.get(lookup_key, value_data)
    if not time_zone:
      return

    try:
      # Catch and warn about unsupported preprocessor plugin.
      knowledge_base.SetTimeZone(time_zone)
      result = True
    except ValueError:
      # TODO: add and store preprocessing errors.
      time_zone = value_data
      logging.warning(u'Unable to map: "{0:s}" to time zone'.format(value_data))

    return result


class WindowsUserAccountsPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """The Windows user account plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsRegistryProfiles'

  def _GetUsernameFromProfilePath(self, path):
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

  def _ParseKey(self, knowledge_base, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    user_account = artifacts.UserAccountArtifact(
        identifier=registry_key.name)

    registry_value = registry_key.GetValueByName(u'ProfileImagePath')
    if registry_value:
      profile_path = registry_value.GetDataAsObject()
      username = self._GetUsernameFromProfilePath(profile_path)

      user_account.user_directory = profile_path or None
      user_account.username = username or None

    try:
      knowledge_base.AddUserAccount(user_account)
    except KeyError:
      # TODO: add and store preprocessing errors.
      pass

    return False


class WindowsWinDirEnvironmentVariablePlugin(
    WindowsPathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %WinDir% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = u'WindowsEnvironmentVariableWinDir'

  _NAME = u'windir'


manager.PreprocessPluginsManager.RegisterPlugins([
    WindowsCodepagePlugin, WindowsHostnamePlugin,
    WindowsProgramFilesEnvironmentVariablePlugin,
    WindowsProgramFilesX86EnvironmentVariablePlugin,
    WindowsSystemProductPlugin, WindowsSystemRootEnvironmentVariablePlugin,
    WindowsSystemVersionPlugin, WindowsTimeZonePlugin,
    WindowsWinDirEnvironmentVariablePlugin, WindowsUserAccountsPlugin])
