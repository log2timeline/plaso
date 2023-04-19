# -*- coding: utf-8 -*-
"""Helper to create filters based on forensic artifact definitions."""

from artifacts import definitions as artifact_types

from dfvfs.helpers import file_system_searcher as dfvfs_file_system_searcher

from dfwinreg import registry_searcher as dfwinreg_registry_searcher

from plaso.engine import logger
from plaso.engine import path_helper


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

  def _BuildFindSpecsFromArtifact(
      self, definition, environment_variables, user_accounts):
    """Builds find specifications from an artifact definition.

    Args:
      definition (artifacts.ArtifactDefinition): artifact definition.
      environment_variables (list[EnvironmentVariableArtifact]):
          environment variables.
      user_accounts (list[UserAccountArtifact]): user accounts.

    Returns:
      list[dfvfs.FindSpec|dfwinreg.FindSpec]: dfVFS or dfWinReg find
          specifications.
    """
    find_specs = []
    for source in definition.sources:
      if source.type_indicator == artifact_types.TYPE_INDICATOR_FILE:
        for path_entry in set(source.paths):
          specifications = self._BuildFindSpecsFromFileSourcePath(
              path_entry, source.separator, environment_variables,
              user_accounts)
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
            'Windows Registry values are not supported, extracting keys: '
            '"{0!s}"').format(key_paths_string))

        for key_path in key_paths:
          if ArtifactDefinitionsFiltersHelper.CheckKeyCompatibility(key_path):
            specifications = self._BuildFindSpecsFromRegistrySourceKey(key_path)
            find_specs.extend(specifications)
            self.registry_artifact_names.add(definition.name)

      elif (source.type_indicator ==
            artifact_types.TYPE_INDICATOR_ARTIFACT_GROUP):
        for name in source.names:
          specifications = self._BuildFindSpecsFromGroupName(
              name, environment_variables, user_accounts)
          find_specs.extend(specifications)

      else:
        logger.warning(
            'Unsupported artifact definition source type: "{0:s}"'.format(
                source.type_indicator))

    return find_specs

  def _BuildFindSpecsFromGroupName(
      self, group_name, environment_variables, user_accounts):
    """Builds find specifications from a artifact group name.

    Args:
      group_name (str): artifact group name.
      environment_variables (list[EnvironmentVariableArtifact]):
          environment variables.
      user_accounts (list[UserAccountArtifact]): user accounts.

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
        definition, environment_variables, user_accounts)

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
      logger.debug('building find spec from key path glob: {0:s}'.format(
          key_path_glob))

      key_path_glob_upper = key_path_glob.upper()
      if key_path_glob_upper.startswith(
          'HKEY_LOCAL_MACHINE\\SYSTEM\\CURRENTCONTROLSET'):
        # Rewrite CurrentControlSet to ControlSet* for Windows NT.
        key_path_glob = 'HKEY_LOCAL_MACHINE\\System\\ControlSet*{0:s}'.format(
            key_path_glob[43:])

      elif key_path_glob_upper.startswith('HKEY_USERS\\%%USERS.SID%%'):
        key_path_glob = 'HKEY_CURRENT_USER{0:s}'.format(key_path_glob[26:])

      find_spec = dfwinreg_registry_searcher.FindSpec(
          key_path_glob=key_path_glob)
      find_specs.append(find_spec)

    return find_specs

  def _BuildFindSpecsFromFileSourcePath(
      self, source_path, path_separator, environment_variables, user_accounts):
    """Builds find specifications from a file source type.

    Args:
      source_path (str): file system path defined by the source.
      path_separator (str): file system path segment separator.
      environment_variables (list[EnvironmentVariableArtifact]):
          environment variables.
      user_accounts (list[UserAccountArtifact]): user accounts.

    Returns:
      list[dfvfs.FindSpec]: find specifications for the file source type.
    """
    find_specs = []
    for path_glob in path_helper.PathHelper.ExpandGlobStars(
        source_path, path_separator):
      logger.debug('building find spec from path glob: {0:s}'.format(
          path_glob))

      for path in path_helper.PathHelper.ExpandUsersVariablePath(
          path_glob, path_separator, user_accounts):
        logger.debug('building find spec from path: {0:s}'.format(path))

        if '%' in path:
          path = path_helper.PathHelper.ExpandWindowsPath(
              path, environment_variables)
          logger.debug('building find spec from expanded path: {0:s}'.format(
              path))

        if not path.startswith(path_separator):
          logger.warning((
              'The path filter must be defined as an absolute path: '
              '"{0:s}"').format(path))
          continue

        try:
          find_spec = dfvfs_file_system_searcher.FindSpec(
              case_sensitive=False, location_glob=path,
              location_separator=path_separator)
        except ValueError as exception:
          logger.error((
              'Unable to build find specification for path: "{0:s}" with '
              'error: {1!s}').format(path, exception))
          continue

        find_specs.append(find_spec)

    return find_specs

  def BuildFindSpecs(
      self, artifact_filter_names, environment_variables=None,
      user_accounts=None):
    """Builds find specifications from artifact definitions.

    Args:
      artifact_filter_names (list[str]): names of artifact definitions that are
          used for filtering file system and Windows Registry key paths.
      environment_variables (Optional[list[EnvironmentVariableArtifact]]):
          environment variables.
      user_accounts (Optional[list[UserAccountArtifact]]): user accounts.
    """
    find_specs = []
    for name in artifact_filter_names:
      definition = self._artifacts_registry.GetDefinitionByName(name)
      if not definition:
        definition = self._artifacts_registry.GetDefinitionByAlias(name)
      if not definition:
        logger.debug('undefined artifact definition: {0:s}'.format(name))
        continue

      logger.debug('building find spec from artifact definition: {0:s}'.format(
          name))
      artifact_find_specs = self._BuildFindSpecsFromArtifact(
          definition, environment_variables, user_accounts)
      find_specs.extend(artifact_find_specs)

    for find_spec in find_specs:
      if isinstance(find_spec, dfvfs_file_system_searcher.FindSpec):
        self.file_system_find_specs.append(find_spec)

      elif isinstance(find_spec, dfwinreg_registry_searcher.FindSpec):
        self.registry_find_specs.append(find_spec)

      else:
        logger.warning('Unsupported find specification type: {0!s}'.format(
            type(find_spec)))

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

    logger.warning('Key path: "{0:s}" is currently not supported'.format(
        key_path))
    return False
