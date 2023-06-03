# -*- coding: utf-8 -*-
"""This file contains classes used for preprocessing in plaso."""

import abc

from dfwinreg import registry_searcher

from artifacts import definitions as artifact_definitions
from dfvfs.helpers import file_system_searcher

from plaso.lib import errors


class ArtifactPreprocessorPlugin(object):
  """The artifact preprocessor plugin interface.

  The artifact preprocessor determines preprocessing attributes based on
  an artifact definition defined by ARTIFACT_DEFINITION_NAME.
  """

  ARTIFACT_DEFINITION_NAME = None


class FileSystemArtifactPreprocessorPlugin(ArtifactPreprocessorPlugin):
  """File system artifact preprocessor plugin interface.

  Shared functionality for preprocessing attributes based on a file system
  artifact definition, such as file or path.
  """

  @abc.abstractmethod
  def _ParsePathSpecification(
      self, mediator, searcher, file_system, path_specification,
      path_separator):
    """Parses a file system for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      path_specification (dfvfs.PathSpec): path specification that contains
          the artifact value data.
      path_separator (str): path segment separator.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """

  def Collect(self, mediator, artifact_definition, searcher, file_system):
    """Collects values using a file artifact definition.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      artifact_definition (artifacts.ArtifactDefinition): artifact definition.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    last_exception = None

    for source in artifact_definition.sources:
      if source.type_indicator not in (
          artifact_definitions.TYPE_INDICATOR_FILE,
          artifact_definitions.TYPE_INDICATOR_PATH):
        continue

      for path in source.paths:
        find_spec = file_system_searcher.FindSpec(
            case_sensitive=False, location_glob=path,
            location_separator=source.separator)

        for path_specification in searcher.Find(find_specs=[find_spec]):
          try:
            self._ParsePathSpecification(
                mediator, searcher, file_system, path_specification,
                source.separator)

            last_exception = None
          except errors.PreProcessFail as exception:
            last_exception = exception

    if last_exception:
      # Only raise an exception if none of the sources were successfully
      # pre-processed.
      raise last_exception


class FileEntryArtifactPreprocessorPlugin(FileSystemArtifactPreprocessorPlugin):
  """File entry artifact preprocessor plugin interface.

  Shared functionality for preprocessing attributes based on a file entry
  artifact definition, such as file or path.
  """

  @abc.abstractmethod
  def _ParseFileEntry(self, mediator, file_entry):
    """Parses a file entry for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_entry (dfvfs.FileEntry): file entry that contains the artifact
          value data.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """

  def _ParsePathSpecification(
      self, mediator, searcher, file_system, path_specification,
      path_separator):
    """Parses a file system for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      path_specification (dfvfs.PathSpec): path specification that contains
          the artifact value data.
      path_separator (str): path segment separator.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    try:
      file_entry = searcher.GetFileEntryByPathSpec(path_specification)
    except IOError as exception:
      relative_path = searcher.GetRelativePath(path_specification)
      if path_separator != file_system.PATH_SEPARATOR:
        relative_path_segments = file_system.SplitPath(relative_path)
        relative_path = '{0:s}{1:s}'.format(
            path_separator, path_separator.join(relative_path_segments))

      raise errors.PreProcessFail((
          'Unable to retrieve file entry: {0:s} with error: '
          '{1!s}').format(relative_path, exception))

    if file_entry:
      mediator.SetFileEntry(file_entry)
      self._ParseFileEntry(mediator, file_entry)


class FileArtifactPreprocessorPlugin(FileEntryArtifactPreprocessorPlugin):
  """File artifact preprocessor plugin interface.

  Shared functionality for preprocessing attributes based on a file artifact
  definition, such as file or path.
  """

  @abc.abstractmethod
  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """

  def _ParseFileEntry(self, mediator, file_entry):
    """Parses a file entry for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_entry (dfvfs.FileEntry): file entry that contains the artifact
          value data.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    if not file_entry.IsFile():
      raise errors.PreProcessFail((
          'Unable to read: {0:s} with error: file entry is not a regular '
          'file').format(self.ARTIFACT_DEFINITION_NAME))

    file_object = file_entry.GetFileObject()
    self._ParseFileData(mediator, file_object)


class WindowsRegistryKeyArtifactPreprocessorPlugin(ArtifactPreprocessorPlugin):
  """Windows Registry key artifact preprocessor plugin interface.

  Shared functionality for preprocessing attributes based on a Windows
  Registry artifact definition, such as Windows Registry key or value.
  """

  @abc.abstractmethod
  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """

  def Collect(
      self, mediator, artifact_definition, searcher):
    """Collects values using a Windows Registry value artifact definition.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      artifact_definition (artifacts.ArtifactDefinition): artifact definition.
      searcher (dfwinreg.WinRegistrySearcher): Windows Registry searcher to
          preprocess the Windows Registry.

    Raises:
      PreProcessFail: if the Windows Registry key or value cannot be read.
    """
    for source in artifact_definition.sources:
      if source.type_indicator not in (
          artifact_definitions.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY,
          artifact_definitions.TYPE_INDICATOR_WINDOWS_REGISTRY_VALUE):
        continue

      if source.type_indicator == (
          artifact_definitions.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY):
        key_value_pairs = [{'key': key} for key in source.keys]
      else:
        key_value_pairs = source.key_value_pairs

      for key_value_pair in key_value_pairs:
        key_path = key_value_pair['key']

        # The artifact definitions currently incorrectly define
        # CurrentControlSet so we correct it here for now.
        # Also see: https://github.com/ForensicArtifacts/artifacts/issues/120
        key_path_upper = key_path.upper()
        if key_path_upper.startswith('%%CURRENT_CONTROL_SET%%'):
          key_path = '{0:s}{1:s}'.format(
              'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet', key_path[23:])

        find_spec = registry_searcher.FindSpec(key_path_glob=key_path)

        for key_path in searcher.Find(find_specs=[find_spec]):
          try:
            registry_key = searcher.GetKeyByPath(key_path)
          except IOError as exception:
            raise errors.PreProcessFail((
                'Unable to retrieve Windows Registry key: {0:s} with error: '
                '{1!s}').format(key_path, exception))

          if registry_key:
            value_name = key_value_pair.get('value', None)
            self._ParseKey(mediator, registry_key, value_name)


class WindowsRegistryValueArtifactPreprocessorPlugin(
    WindowsRegistryKeyArtifactPreprocessorPlugin):
  """Windows Registry value artifact preprocessor plugin interface.

  Shared functionality for preprocessing attributes based on a Windows
  Registry value artifact definition.
  """

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value or None if not
          specified.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    try:
      registry_value = registry_key.GetValueByName(value_name)
    except IOError as exception:
      raise errors.PreProcessFail((
          'Unable to retrieve Windows Registry key: {0:s} value: {1:s} '
          'with error: {2!s}').format(
              registry_key.path, value_name, exception))

    if registry_value:
      value_object = registry_value.GetDataAsObject()
      if value_object:
        self._ParseValueData(mediator, value_object)

  @abc.abstractmethod
  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      value_data (object): Windows Registry value data.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """


# TODO: rename class.
class KnowledgeBasePreprocessorPlugin(object):
  """The knowledge base preprocessor plugin interface.

  The knowledge base preprocessor determines preprocessing attributes based on
  other values in the knowledge base.
  """

  @abc.abstractmethod
  def Collect(self, mediator):
    """Collects values from the knowledge base.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
