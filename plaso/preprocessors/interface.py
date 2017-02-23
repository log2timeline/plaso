# -*- coding: utf-8 -*-
"""This file contains classes used for preprocessing in plaso."""

import abc

from dfvfs.helpers import file_system_searcher

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import py2to3


class PreprocessPlugin(object):
  """The preprocess plugin interface."""

  @property
  def plugin_name(self):
    """str: name of the plugin."""
    return self.__class__.__name__


class FileSystemPreprocessPlugin(PreprocessPlugin):
  """The file system preprocess plugin interface."""

  def _FindFileEntry(self, searcher, path):
    """Searches for a file entry that matches the path.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      path (str): location of the file entry relative to the file system
          of the searcher.

    Returns:
      dfvfs.FileEntry: file entry if successful or None otherwise.

    Raises:
      errors.PreProcessFail: if the file entry cannot be opened.
    """
    path_specs = self._FindPathSpecs(searcher, path)
    if not path_specs or len(path_specs) != 1:
      return

    try:
      return searcher.GetFileEntryByPathSpec(path_specs[0])
    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to retrieve file entry: {0:s} with error: {1:s}'.format(
              path, exception))

  def _FindPathSpecs(self, searcher, path):
    """Searches for path specifications that matches the path.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      path (str): location of the file entry relative to the file system
          of the searcher.

    Returns:
      list[dfvfs.PathSpec]: path specifcations.
    """
    find_spec = file_system_searcher.FindSpec(
        location_regex=path, case_sensitive=False)
    return list(searcher.Find(find_specs=[find_spec]))

  @abc.abstractmethod
  def Run(self, searcher, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
    """


class FilePreprocessPlugin(FileSystemPreprocessPlugin):
  """The file preprocess plugin interface."""

  _PATH = None

  @abc.abstractmethod
  def _ParseFileObject(self, knowledge_base, file_object):
    """Parses a file-like object.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object.
    """

  def Run(self, searcher, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
    """
    file_entry = self._FindFileEntry(searcher, self._PATH)
    if not file_entry:
      return

    file_object = file_entry.GetFileObject()
    try:
      self._ParseFileObject(knowledge_base, file_object)
    finally:
      file_object.close()


class WindowsPathEnvironmentVariablePlugin(FileSystemPreprocessPlugin):
  """Windows path environment variable preprocess plugin interface."""

  _NAME = None
  _PATH_REGEX = None

  def Run(self, searcher, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    path_specs = self._FindPathSpecs(searcher, self._PATH_REGEX)
    if not path_specs:
      return

    relative_path = searcher.GetRelativePath(path_specs[0])
    if not relative_path:
      raise errors.PreProcessFail(
          u'Missing relative path for: {0:s}'.format(self._PATH_REGEX))

    if relative_path.startswith(u'/'):
      path_segments = relative_path.split(u'/')
      relative_path = u'\\'.join(path_segments)

    evironment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=relative_path)

    try:
      knowledge_base.AddEnvironmentVariable(evironment_variable)
    except KeyError:
      # TODO: add and store preprocessing errors.
      pass


class WindowsRegistryKeyPreprocessPlugin(PreprocessPlugin):
  """Windows Registry key preprocess plugin interface."""

  _REGISTRY_KEY_PATH = None

  @abc.abstractmethod
  def _ParseKey(self, knowledge_base, registry_key):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      registry_key (WinRegistryKey): Windows Registry key.
    """

  def Run(self, win_registry, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      win_registry (WinRegistry): Windows Registry.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Raises:
      PreProcessFail: if there was an error retrieving the Registry key.
    """
    try:
      registry_key = win_registry.GetKeyByPath(self._REGISTRY_KEY_PATH)

    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to retrieve Registry key: {0:s} with error: {1:s}'.format(
              self._REGISTRY_KEY_PATH, exception))

    if registry_key:
      self._ParseKey(knowledge_base, registry_key)


class WindowsRegistryValuePreprocessPlugin(WindowsRegistryKeyPreprocessPlugin):
  """Windows Registry value preprocess plugin interface."""

  _REGISTRY_VALUE_NAME = u''

  def _ParseKey(self, knowledge_base, registry_key):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      registry_key (WinRegistryKey): Windows Registry key.

    Raises:
      errors.PreProcessFail: if the Registry value or value data can not be
          retrieved.
    """
    try:
      registry_value = registry_key.GetValueByName(self._REGISTRY_VALUE_NAME)
    except IOError as exception:
      raise errors.PreProcessFail((
          u'Unable to retrieve Registry key: {0:s}, value: {1:s} with '
          u'error: {2:s}').format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME, exception))

    if not registry_value:
      return

    try:
      value_data = registry_value.GetDataAsObject()
    except IOError as exception:
      raise errors.PreProcessFail((
          u'Unable to retrieve Registry key: {0:s}, value: {1:s} data with '
          u'error: {2:s}').format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME, exception))

    if not value_data:
      return

    self._ParseValueData(knowledge_base, value_data)

  @abc.abstractmethod
  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.
    """


class WindowsRegistryEnvironmentVariable(WindowsRegistryValuePreprocessPlugin):
  """Windows Registry environment variable preprocess plugin interface."""

  def _ParseValueData(self, knowledge_base, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the value data is not supported.
    """
    if not isinstance(value_data, py2to3.UNICODE_TYPE):
      raise errors.PreProcessFail(
          u'Unsupported Registry key: {0:s}, value: {1:s} type.'.format(
              self._REGISTRY_KEY_PATH, self._REGISTRY_VALUE_NAME))

    evironment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=value_data)

    try:
      knowledge_base.AddEnvironmentVariable(evironment_variable)
    except KeyError:
      # TODO: add and store preprocessing errors.
      pass
