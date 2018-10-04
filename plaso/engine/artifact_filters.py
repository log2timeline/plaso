# -*- coding: utf-8 -*-
"""Helper to create filters based on forensic artifact definitions."""

from __future__ import unicode_literals
from collections import defaultdict

from artifacts import definitions as artifact_types

from dfvfs.helpers import file_system_searcher
from dfwinreg import registry_searcher
from plaso.engine import logger
from plaso.engine import path_helper


class ArtifactDefinitionsFilterHelper(object):
  """Helper to create filters based on artifact definitions.

  Builds extraction filters from forensic artifact definitions.

  For more information about Forensic Artifacts see:
  https://github.com/ForensicArtifacts/artifacts/blob/master/docs/Artifacts%20definition%20format%20and%20style%20guide.asciidoc
  """

  KNOWLEDGE_BASE_VALUE = 'ARTIFACT_FILTERS'

  _COMPATIBLE_REGISTRY_KEY_PATH_PREFIXES = frozenset([
      'HKEY_LOCAL_MACHINE\\SYSTEM',
      'HKEY_LOCAL_MACHINE\\SOFTWARE',
      'HKEY_LOCAL_MACHINE\\SAM',
      'HKEY_LOCAL_MACHINE\\SECURITY'])

  def __init__(self, artifacts_registry, artifact_filters, knowledge_base):
    """Initializes an artifact definitions filter helper.

    Args:
      artifacts_registry (artifacts.ArtifactDefinitionsRegistry): artifact
          definitions registry.
      artifact_filters (list[str]): names of artifact definitions that are
          used for filtering file system and Windows Registry key paths.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for filtering.
    """
    super(ArtifactDefinitionsFilterHelper, self).__init__()
    self._artifacts = artifact_filters
    self._artifacts_registry = artifacts_registry
    self._knowledge_base = knowledge_base
    self._find_specs_per_source_type = defaultdict(list)

  @staticmethod
  def CheckKeyCompatibility(key_path):
    """Checks if a Windows Registry key path is supported by dfWinReg.

    Args:
      key_path (str): path of the Windows Registry key.

    Returns:
      bool: True if key is compatible or False if not.
    """
    for key_path_prefix in (
        ArtifactDefinitionsFilterHelper._COMPATIBLE_REGISTRY_KEY_PATH_PREFIXES):
      key_path = key_path.upper()
      if key_path.startswith(key_path_prefix):
        return True

    logger.warning(
        'Prefix of key "{0:s}" is currently not supported'.format(key_path))
    return False

  def BuildFindSpecs(self, environment_variables=None):
    """Builds find specifications from artifact definitions.

    The resulting find specifications are set in the knowledge base.

    Args:
      environment_variables (Optional[list[EnvironmentVariableArtifact]]):
          environment variables.
    """
    for name in self._artifacts:
      definition = self._artifacts_registry.GetDefinitionByName(name)
      if not definition:
        continue

      for source in definition.sources:
        if source.type_indicator == artifact_types.TYPE_INDICATOR_FILE:
          # TODO: move source.paths iteration into
          # BuildFindSpecsFromFileArtifact.
          for path_entry in set(source.paths):
            find_specs = self.BuildFindSpecsFromFileArtifact(
                path_entry, source.separator, environment_variables,
                self._knowledge_base.user_accounts)
            artifact_group = self._find_specs_per_source_type[
                artifact_types.TYPE_INDICATOR_FILE]
            artifact_group.extend(find_specs)

        elif (source.type_indicator ==
              artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY):
          # TODO: move source.keys iteration into
          # BuildFindSpecsFromRegistryArtifact.
          for key_path in set(source.keys):
            if self.CheckKeyCompatibility(key_path):
              find_specs = self.BuildFindSpecsFromRegistryArtifact(key_path)
              artifact_group = self._find_specs_per_source_type[
                  artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY]
              artifact_group.extend(find_specs)

        elif (source.type_indicator ==
              artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_VALUE):
          # TODO: Handle Registry Values Once Supported in dfwinreg.
          # https://github.com/log2timeline/dfwinreg/issues/98
          logger.warning((
              'Windows Registry values are not supported, extracting key: '
              '"{0!s}"').format(source.key_value_pairs))

          # TODO: move source.key_value_pairs iteration into
          # BuildFindSpecsFromRegistryArtifact.
          for key_path in set([
              key_value['key'] for key_value in source.key_value_pairs]):
            if self.CheckKeyCompatibility(key_path):
              find_specs = self.BuildFindSpecsFromRegistryArtifact(key_path)
              artifact_group = self._find_specs_per_source_type[
                  artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY]
              artifact_group.extend(find_specs)

        elif (source.type_indicator ==
              artifact_types.TYPE_INDICATOR_ARTIFACT_GROUP):
          self._artifacts.remove(name)
          for name_entry in set(source.names):
            self._artifacts.append(name_entry)
          self.BuildFindSpecs(environment_variables=environment_variables)

        else:
          logger.warning(
              'Unsupported artifact definition source type: "{0:s}"'.format(
                  source.type_indicator))

    self._knowledge_base.SetValue(
        self.KNOWLEDGE_BASE_VALUE, self._find_specs_per_source_type)

  def BuildFindSpecsFromFileArtifact(
      self, source_path, path_separator, environment_variables, user_accounts):
    """Builds find specifications from a file source type.

    Args:
      source_path (str): file system path defined by the source.
      path_separator (str): file system path segment separator.
      environment_variables (list[str]): environment variable attributes used to
          dynamically populate environment variables in key.
      user_accounts (list[str]): identified user accounts stored in the
          knowledge base.

    Returns:
      list[dfvfs.FindSpec]: find specifications for the file source type.
    """
    find_specs = []
    for glob_path in path_helper.PathHelper.ExpandRecursiveGlobs(
        source_path, path_separator):
      for path in path_helper.PathHelper.ExpandUsersHomeDirectoryPath(
          glob_path, user_accounts):
        if '%' in path:
          path = path_helper.PathHelper.ExpandWindowsPath(
              path, environment_variables)

        if not path.startswith(path_separator):
          logger.warning((
              'The path filter must be defined as an absolute path: '
              '"{0:s}"').format(path))
          continue

        # Convert the path filters into a list of path segments and
        # strip the root path segment.
        path_segments = path.split(path_separator)

        # Remove initial root entry
        path_segments.pop(0)

        if not path_segments[-1]:
          logger.warning(
              'Empty last path segment in path filter: "{0:s}"'.format(path))
          path_segments.pop(-1)

        try:
          find_spec = file_system_searcher.FindSpec(
              location_glob=path_segments, case_sensitive=False)
        except ValueError as exception:
          logger.error((
              'Unable to build find specification for path: "{0:s}" with '
              'error: {1!s}').format(path, exception))
          continue

        find_specs.append(find_spec)

    return find_specs

  def BuildFindSpecsFromRegistryArtifact(self, source_key_path):
    """Build find specifications from a Windows Registry source type.

    Args:
      source_key_path (str): Windows Registry key path defined by the source.

    Returns:
      list[dfwinreg.FindSpec]: find specifications for the Windows Registry
          source type.
    """
    find_specs = []
    for key_path in path_helper.PathHelper.ExpandRecursiveGlobs(
        source_key_path, '\\'):
      if '%%' in key_path:
        logger.error('Unable to expand key path: "{0:s}"'.format(key_path))
        continue

      find_spec = registry_searcher.FindSpec(key_path_glob=key_path)
      find_specs.append(find_spec)

    return find_specs
