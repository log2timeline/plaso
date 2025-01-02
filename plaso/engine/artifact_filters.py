# -*- coding: utf-8 -*-
"""Helper to create filters based on forensic artifact definitions."""

import os
from artifacts import definitions as artifact_types

from dfvfs.helpers import file_system_searcher as dfvfs_file_system_searcher

from dfwinreg import registry_searcher as dfwinreg_registry_searcher

from plaso.engine import logger
from plaso.engine import path_helper
from plaso.engine import artifacts_trie


class ArtifactDefinitionsFiltersHelper(object):
  """Helper to create collection filters based on artifact definitions.

  Builds collection filters from forensic artifact definitions.

  For more information about Forensic Artifacts see:
  https://github.com/ForensicArtifacts/artifacts/blob/main/docs/Artifacts%20definition%20format%20and%20style%20guide.asciidoc

  Attributes:
    file_system_artifact_names (set[str]): names of artifacts definitions that
        generated file system find specifications.
    file_system_find_specs (list[dfvfs.FindSpec]): file system find
        specifications of paths to include in the collection.
    registry_artifact_names (set[str]): names of artifacts definitions that
        generated Windows Registry find specifications.
    registry_find_specs (list[dfwinreg.FindSpec]): Windows Registry find
        specifications.
    registry_find_specs_artifact_names (list[]str): Windows Registry artifact
        names corresponding to the find specifications.
    artifacts_trie (ArtifactsTrie): Trie structure for storing artifact
        definitionpaths.
  """

  _COMPATIBLE_REGISTRY_KEY_PATH_PREFIXES = frozenset([
      'HKEY_CURRENT_USER',
      'HKEY_LOCAL_MACHINE\\SYSTEM',
      'HKEY_LOCAL_MACHINE\\SOFTWARE',
      'HKEY_LOCAL_MACHINE\\SAM',
      'HKEY_LOCAL_MACHINE\\SECURITY',
      'HKEY_USERS'])

  def __init__(self, artifacts_registry):
    """Initializes an artifact definitions filters helper.

    Args:
      artifacts_registry (artifacts.ArtifactDefinitionsRegistry): artifact
          definitions registry.
    """
    super(ArtifactDefinitionsFiltersHelper, self).__init__()
    self._artifacts_registry = artifacts_registry

    self.file_system_artifact_names = set()
    self.file_system_find_specs = []
    self.registry_artifact_names = set()
    self.registry_find_specs = []
    self.registry_find_specs_artifact_names = []
    self.artifacts_trie = artifacts_trie.ArtifactsTrie()

  def _BuildFindSpecsFromArtifact(
          self,
          definition,
          environment_variables,
          user_accounts,
          enable_artifacts_map=False,
          original_registery_artifact_filter_names=None):
    """Builds find specifications from an artifact definition.

    Args:
      definition (artifacts.ArtifactDefinition): artifact definition.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.
      user_accounts (list[UserAccountArtifact]): user accounts.
      enable_artifacts_map (Optional[bool]): True if the artifacts path map
          should be generated. Defaults to False.
      original_registery_artifact_filter_names (Optional[set[str]]): Set of
          original registery filter names, used in case registery hive files
          are being requested as a result of a previous filter.

    Returns:
      list[dfvfs.FindSpec|dfwinreg.FindSpec]: dfVFS or dfWinReg find
          specifications.
    """
    find_specs = []
    for source in definition.sources:
      if source.type_indicator == artifact_types.TYPE_INDICATOR_FILE:
        for path_entry in set(source.paths):
          specifications = self._BuildFindSpecsFromFileSourcePath(
              definition.name,
              path_entry,
              source.separator,
              environment_variables,
              user_accounts,
              enable_artifacts_map=enable_artifacts_map,
              original_registery_artifact_filter_names=(
                  original_registery_artifact_filter_names))
          find_specs.extend(specifications)
          self.file_system_artifact_names.add(definition.name)

      elif (source.type_indicator ==
            artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY):
        for key_path in set(source.keys):
          if ArtifactDefinitionsFiltersHelper.CheckKeyCompatibility(key_path):
            specifications = self._BuildFindSpecsFromRegistrySourceKey(key_path)
            find_specs.extend(specifications)
            self.registry_artifact_names.add(definition.name)

      elif (source.type_indicator ==
            artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_VALUE):
        # TODO: Handle Registry Values Once Supported in dfwinreg.
        # https://github.com/log2timeline/dfwinreg/issues/98

        # Use set-comprehension to create a set of the source key paths.
        key_paths = {key_value['key'] for key_value in source.key_value_pairs}
        key_paths_string = ', '.join(key_paths)

        logger.warning((
            f'Windows Registry values are not supported, extracting keys: '
            f'"{key_paths_string!s}"'))

        for key_path in key_paths:
          if ArtifactDefinitionsFiltersHelper.CheckKeyCompatibility(key_path):
            specifications = self._BuildFindSpecsFromRegistrySourceKey(key_path)
            find_specs.extend(specifications)
            self.registry_artifact_names.add(definition.name)

      elif (source.type_indicator ==
            artifact_types.TYPE_INDICATOR_ARTIFACT_GROUP):
        for name in source.names:
          specifications = self._BuildFindSpecsFromGroupName(
              name,
              environment_variables,
              user_accounts,
              enable_artifacts_map=enable_artifacts_map,
              original_registery_artifact_filter_names=(
                  original_registery_artifact_filter_names))
          find_specs.extend(specifications)

      else:
        logger.warning((
            f'Unsupported artifact definition source type: '
            f'"{source.type_indicator:s}"'))

    return find_specs

  def _BuildFindSpecsFromGroupName(
          self,
          group_name,
          environment_variables,
          user_accounts,
          enable_artifacts_map=False,
          original_registery_artifact_filter_names=None):
    """Builds find specifications from a artifact group name.

    Args:
      group_name (str): artifact group name.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.
      user_accounts (list[UserAccountArtifact]): user accounts.
      enable_artifacts_map (Optional[bool]): True if the artifacts path map
          should be generated. Defaults to False.
      original_registery_artifact_filter_names (Optional[set[str]]): Set of
          original registery filter names, used in case registery hive files
          are being requested as a result of a previous filter.

    Returns:
      list[dfwinreg.FindSpec|dfvfs.FindSpec]: find specifications or None if no
          artifact with the given name can be retrieved.
    """
    definition = self._artifacts_registry.GetDefinitionByName(group_name)
    if not definition:
      definition = self._artifacts_registry.GetDefinitionByAlias(group_name)
    if not definition:
      return None

    return self._BuildFindSpecsFromArtifact(
        definition,
        environment_variables,
        user_accounts,
        enable_artifacts_map=enable_artifacts_map,
        original_registery_artifact_filter_names=(
            original_registery_artifact_filter_names))

  def _BuildFindSpecsFromRegistrySourceKey(self, key_path):
    """Build find specifications from a Windows Registry source type.

    Args:
      key_path (str): Windows Registry key path defined by the source.

    Returns:
      list[dfwinreg.FindSpec]: find specifications for the Windows Registry
          source type.
    """
    find_specs = []
    for key_path_glob in path_helper.PathHelper.ExpandGlobStars(key_path, '\\'):
      logger.debug(f'building find spec from key path glob: {key_path_glob:s}')

      key_path_glob_upper = key_path_glob.upper()
      if key_path_glob_upper.startswith(
          'HKEY_LOCAL_MACHINE\\SYSTEM\\CURRENTCONTROLSET'):
        # Rewrite CurrentControlSet to ControlSet* for Windows NT.
        key_path_glob = ''.join([
            'HKEY_LOCAL_MACHINE\\System\\ControlSet*', key_path_glob[43:]])

      elif key_path_glob_upper.startswith('HKEY_USERS\\%%USERS.SID%%'):
        # Escaping charachter excluded from string index.
        key_path_glob = ''.join(['HKEY_CURRENT_USER', key_path_glob[24:]])

      find_spec = dfwinreg_registry_searcher.FindSpec(
          key_path_glob=key_path_glob)
      find_specs.append(find_spec)

    return find_specs

  def _BuildFindSpecsFromFileSourcePath(
          self,
          artifact_name,
          source_path,
          path_separator,
          environment_variables,
          user_accounts,
          enable_artifacts_map=False,
          original_registery_artifact_filter_names=None):
    """Builds find specifications from a file source type.

    Args:
      artifact_name (str): artifact name.
      source_path (str): file system path defined by the source.
      path_separator (str): file system path segment separator.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.
      user_accounts (list[UserAccountArtifact]): user accounts.
      enable_artifacts_map (Optional[bool]): True if the artifacts path map
          should be generated. Defaults to False.
      original_registery_artifact_filter_names (Optional[set[str]]): Set of
          original registery filter names, used in case registery hive files
          are being requested as a result of a previous filter.

    Returns:
      list[dfvfs.FindSpec]: find specifications for the file source type.
    """
    find_specs = []
    for path_glob in path_helper.PathHelper.ExpandGlobStars(
        source_path, path_separator):
      logger.debug(f'building find spec from path glob: {path_glob:s}')

      for path in path_helper.PathHelper.ExpandUsersVariablePath(
          path_glob, path_separator, user_accounts):
        logger.debug(f'building find spec from path: {path:s}')

        expanded_path = self._ExpandPathVariables(
            path, environment_variables, path_separator)
        if expanded_path is None:
          continue

        find_spec = self._CreateFindSpec(expanded_path, path_separator)
        if find_spec is None:
          continue

        find_specs.append(find_spec)

        if enable_artifacts_map:
          self._AddToArtifactsTrie(artifact_name,
                                   expanded_path,
                                   original_registery_artifact_filter_names,
                                   path_separator)

    return find_specs

  def _AddToArtifactsTrie(
          self,
          artifact_name,
          path,
          original_registery_artifact_filter_names,
          path_separator):
    """Adds a path to the artifacts trie.

    Args:
        artifact_name (str): artifact name.
        path (str): file system path.
        original_registery_artifact_filter_names (Optional[set[str]]): Set of
            original registery filter names.
        path_separator (str): path separator.
    """
    normalized_path = path.replace(path_separator, os.sep)
    self.artifacts_trie.AddPath(artifact_name, normalized_path, os.sep)
    if original_registery_artifact_filter_names:
      for name in original_registery_artifact_filter_names:
        self.artifacts_trie.AddPath(name, normalized_path, os.sep)

  def _ExpandPathVariables(self, path, environment_variables, path_separator):
    """Expands Windows paths and validates the result.

    Args:
      path (str): file system path with environment variables
      environment_variables (list[EnvironmentVariableArtifact]):
          environment variables.
      path_separator (str): file system path segment separator.

    Returns:
      str: expanded path, or None if the path is invalid
    """

    if '%' in path:
      path = path_helper.PathHelper.ExpandWindowsPath(
          path, environment_variables)
      logger.debug(f'building find spec from expanded path: {path:s}')

    if not path.startswith(path_separator):
      logger.warning((
          f'The path filter must be defined as an absolute path: '
          f'"{path:s}"'))
      return None
    return path

  def _CreateFindSpec(self, path, path_separator):
    """Creates a dfVFS find specification.

    Args:
      path (str): Path to match.
      path_separator (str): file system path segment separator.


    Returns:
        dfvfs.FindSpec: a find specification or None if one cannot be created.
    """
    try:
      find_spec = dfvfs_file_system_searcher.FindSpec(
          case_sensitive=False, location_glob=path,
          location_separator=path_separator)
      return find_spec
    except ValueError as exception:
      logger.error((
          f'Unable to build find specification for path: "{path:s}" with '
          f'error: {exception!s}'))
      return None

  def BuildFindSpecs(
          self,
          artifact_filter_names,
          environment_variables=None,
          user_accounts=None,
          enable_artifacts_map=False,
          original_registery_artifact_filter_names=None):
    """Builds find specifications from artifact definitions.

    Args:
      artifact_filter_names (list[str]): names of artifact definitions that are
          used for filtering file system and Windows Registry key paths.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.
      user_accounts (Optional[list[UserAccountArtifact]]): user accounts.
      enable_artifacts_map (Optional[bool]): True if the artifacts path map
          should be generated. Defaults to False.
      original_registery_artifact_filter_names (Optional[set[str]]): Set of
          original registery filter names, used in case registery hive files
          are being requested as a result of a previous filter.
    """
    find_specs = {}
    for name in artifact_filter_names:
      definition = self._artifacts_registry.GetDefinitionByName(name)
      if not definition:
        definition = self._artifacts_registry.GetDefinitionByAlias(name)
      if not definition:
        logger.debug(f'undefined artifact definition: {name:s}')
        continue

      logger.debug(f'building find spec from artifact definition: {name:s}')
      artifact_find_specs = self._BuildFindSpecsFromArtifact(
          definition,
          environment_variables,
          user_accounts,
          enable_artifacts_map=enable_artifacts_map,
          original_registery_artifact_filter_names=(
              original_registery_artifact_filter_names))
      find_specs.setdefault(name, []).extend(artifact_find_specs)

    for name, find_spec_values in find_specs.items():
      for find_spec in find_spec_values:
        if isinstance(find_spec, dfvfs_file_system_searcher.FindSpec):
          self.file_system_find_specs.append(find_spec)

        elif isinstance(find_spec, dfwinreg_registry_searcher.FindSpec):
          self.registry_find_specs.append(find_spec)
          # Artifact names ordered similar to registery find specs
          self.registry_find_specs_artifact_names.append(name)
        else:
          type_string = type(find_spec)
          logger.warning(
              f'Unsupported find specification type: {type_string!s}')

  @classmethod
  def CheckKeyCompatibility(cls, key_path):
    """Checks if a Windows Registry key path is supported by dfWinReg.

    Args:
      key_path (str): path of the Windows Registry key.

    Returns:
      bool: True if key is compatible or False if not.
    """
    key_path_upper = key_path.upper()
    for key_path_prefix in cls._COMPATIBLE_REGISTRY_KEY_PATH_PREFIXES:
      if key_path_upper.startswith(key_path_prefix):
        return True

    logger.warning(f'Key path: "{key_path:s}" is currently not supported')
    return False
