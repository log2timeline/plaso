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
    find_specs = []
    for name in self._artifacts:
      definition = self._artifacts_registry.GetDefinitionByName(name)
      if not definition:
        continue

      artifact_find_specs = self._BuildFindSpecsFromArtifact(
          definition, environment_variables)
      find_specs.extend(artifact_find_specs)

    find_specs_per_source_type = defaultdict(list)
    for find_spec in find_specs:
      if isinstance(find_spec, registry_searcher.FindSpec):
        artifact_list = find_specs_per_source_type[
            artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY]
        artifact_list.append(find_spec)
        continue

      if isinstance(find_spec, file_system_searcher.FindSpec):
        artifact_list = find_specs_per_source_type[
            artifact_types.TYPE_INDICATOR_FILE]
        artifact_list.append(find_spec)
        continue

      logger.warning('Unknown find specification type: {0:s}'.format(
          type(find_spec)))

    self._knowledge_base.SetValue(
        self.KNOWLEDGE_BASE_VALUE, find_specs_per_source_type)

  def _BuildFindSpecsFromArtifact(self, definition, environment_variables):
    """Builds find specifications from an artifact definition.

    Args:
      definition (artifacts.ArtifactDefinition): artifact definition.
      environment_variables (list[EnvironmentVariableArtifact]):
          environment variables.

    Returns:
      list[dfwinreg.FindSpec|dfvfs.FindSpec]: find specifications.
    """
    find_specs = []
    for source in definition.sources:
      if source.type_indicator == artifact_types.TYPE_INDICATOR_FILE:
        for path_entry in set(source.paths):
          specifications = self._BuildFindSpecsFromFileSourcePath(
              path_entry, source.separator, environment_variables,
              self._knowledge_base.user_accounts)
          find_specs.extend(specifications)

      elif (source.type_indicator ==
            artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY):
        for key_path in set(source.keys):
          if self.CheckKeyCompatibility(key_path):
            specifications = self._BuildFindSpecsFromRegistrySourceKey(key_path)
            find_specs.extend(specifications)

      elif (source.type_indicator ==
            artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_VALUE):
        # TODO: Handle Registry Values Once Supported in dfwinreg.
        # https://github.com/log2timeline/dfwinreg/issues/98

        # Use set-comprehension to create a set of the source key paths.
        key_paths = {
            key_value['key'] for key_value in source.key_value_pairs}
        key_paths_string = ', '.join(key_paths)

        logger.warning((
            'Windows Registry values are not supported, extracting keys: '
            '"{0!s}"').format(key_paths_string))

        for key_path in key_paths:
          if self.CheckKeyCompatibility(key_path):
            specifications = self._BuildFindSpecsFromRegistrySourceKey(key_path)
            find_specs.extend(specifications)

      elif (source.type_indicator ==
            artifact_types.TYPE_INDICATOR_ARTIFACT_GROUP):
        for name in source.names:
          specifications = self._BuildFindSpecsFromGroupName(
              name, environment_variables)
          find_specs.extend(specifications)

      else:
        logger.warning(
            'Unsupported artifact definition source type: "{0:s}"'.format(
                source.type_indicator))

      return find_specs

  def _BuildFindSpecsFromGroupName(self, group_name, environment_variables):
    """Builds find specifications from a artifact group name.

    Args:
      group_name (str): artifact group name.
      environment_variables (list[str]): environment variable attributes used to
          dynamically populate environment variables in file and registry
          artifacts.

    Returns:
      list[dfwinreg.FindSpec|dfvfs.FindSpec]: find specifications or None if no
          artifact with the given name can be retrieved.
    """
    definition = self._artifacts_registry.GetDefinitionByName(group_name)
    if not definition:
      return None
    return self._BuildFindSpecsFromArtifact(definition, environment_variables)


  def _BuildFindSpecsFromFileSourcePath(
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
          glob_path, path_separator, user_accounts):
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

  def _BuildFindSpecsFromRegistrySourceKey(self, key_path):
    """Build find specifications from a Windows Registry source type.

    Args:
      key_path (str): Windows Registry key path defined by the source.

    Returns:
      list[dfwinreg.FindSpec]: find specifications for the Windows Registry
          source type.
    """
    find_specs = []
    for key_path_glob in path_helper.PathHelper.ExpandRecursiveGlobs(
        key_path, '\\'):
      if '%%' in key_path_glob:
        logger.error('Unable to expand key path: "{0:s}"'.format(key_path_glob))
        continue

      find_spec = registry_searcher.FindSpec(key_path_glob=key_path_glob)
      find_specs.append(find_spec)

    return find_specs
