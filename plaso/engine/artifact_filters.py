# -*- coding: utf-8 -*-
"""Helper to create filters based on forensic artifact definitions."""

from __future__ import unicode_literals

import logging

from artifacts import definitions as artifact_types

from dfvfs.helpers import file_system_searcher
from dfwinreg import registry_searcher
from plaso.engine import path_helper


class ArtifactDefinitionsFilterHelper(object):
  """Helper to create filters based on artifact definitions.

  Builds extraction filters from forensic artifact definitions.

  For more information about Forensic Artifacts see:
  https://github.com/ForensicArtifacts/artifacts/blob/master/docs/Artifacts%20definition%20format%20and%20style%20guide.asciidoc
  """

  ARTIFACT_FILTERS = 'ARTIFACT_FILTERS'
  _COMPATIBLE_DFWINREG_KEYS = ('HKEY_LOCAL_MACHINE')

  def __init__(self, artifacts_registry, artifacts, knowledge_base):
    """Initializes an artifact definitions filter helper.

    Args:
      artifacts_registry (artifacts.ArtifactDefinitionsRegistry]): artifact
          definitions registry.
      artifacts (list[str]): artifact names to process.
      path (str): path to a file that contains one or more forensic artifacts.
      knowledge_base (KnowledgeBase): Knowledge base for Log2Timeline.
    """
    super(ArtifactDefinitionsFilterHelper, self).__init__()
    self._artifacts_registry = artifacts_registry
    self._artifacts = artifacts
    self._knowledge_base = knowledge_base

  def BuildFindSpecs(self, environment_variables=None):
    """Builds find specification from a forensic artifact definitions.

    Args:
      environment_variables (Optional[list[EnvironmentVariableArtifact]]):
          environment variables.
    """
    find_specs = {}

    artifact_definitions = []
    for artifact_filter in self._artifacts:
      if self._artifacts_registry.GetDefinitionByName(artifact_filter):
        artifact_definitions.append(
            self._artifacts_registry.GetDefinitionByName(artifact_filter))

    for definition in artifact_definitions:
      for source in definition.sources:
        if source.type_indicator == artifact_types.TYPE_INDICATOR_FILE:
          for path_entry in source.paths:
            self.BuildFindSpecsFromFileArtifact(
                path_entry, source.separator, environment_variables,
                self._knowledge_base.user_accounts, find_specs)
        elif (source.type_indicator ==
              artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY):
          keys = set(source.keys)
          for key_entry in keys:
            if self._CheckKeyCompatibility(key_entry):
              self.BuildFindSpecsFromRegistryArtifact(
                  key_entry, find_specs)
        elif (source.type_indicator ==
              artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_VALUE):
          # TODO: Handle Registry Values Once Supported in dfwinreg.
          # https://github.com/log2timeline/dfwinreg/issues/98
          logging.warning(('Unable to handle Registry Value, extracting '
                           'key only: "{0:s}"').format(source.key_value_pairs))

          for key_pair in source.key_value_pairs:
            keys = set()
            keys.add(key_pair.get('key'))
            for key_entry in keys:
              if self._CheckKeyCompatibility(key_entry):
                self.BuildFindSpecsFromRegistryArtifact(key_entry, find_specs)
        else:
          logging.warning(('Unable to handle artifact, plaso does not '
                           'support: "{0:s}"').format(source.type_indicator))

    self._knowledge_base.SetValue(self.ARTIFACT_FILTERS, find_specs)

  @classmethod
  def BuildFindSpecsFromFileArtifact(
      cls, path_entry, separator, environment_variables, user_accounts,
      find_specs):
    """Build find specifications from a FILE artifact type.

    Args:
      path_entry (str):  Current file system path to add.
          environment variables.
      separator (str): File system path separator.
      environment_variables list(str):  Environment variable attributes used to
          dynamically populate environment variables in key.
      user_accounts list(str): Identified user accounts stored in the
          knowledge base.
      find_specs dict[artifacts.artifact_types]:  Dictionary containing
          find_specs.
    """
    for glob_path in path_helper.PathHelper.ExpandRecursiveGlobs(
        path_entry, separator):
      for path in path_helper.PathHelper.ExpandUserHomeDirectoryPath(
          glob_path, user_accounts):
        if '%' in path:
          path = path_helper.PathHelper.ExpandWindowsPath(
              path, environment_variables)

        if not path.startswith(separator):
          logging.warning((
              'The path filter must be defined as an absolute path: '
              '"{0:s}"').format(path))
          continue

        # Convert the path filters into a list of path segments and
        # strip the root path segment.
        path_segments = path.split(separator)

        # Remove initial root entry
        path_segments.pop(0)

        if not path_segments[-1]:
          logging.warning(
              'Empty last path segment in path filter: "{0:s}"'.format(path))
          path_segments.pop(-1)

        try:
          find_spec = file_system_searcher.FindSpec(
              location_glob=path_segments, case_sensitive=False)
        except ValueError as exception:
          logging.error((
              'Unable to build find spec for path: "{0:s}" with error: "{1!s}"'
          ).format(path, exception))
          continue
        if artifact_types.TYPE_INDICATOR_FILE not in find_specs:
          find_specs[artifact_types.TYPE_INDICATOR_FILE] = []
        find_specs[artifact_types.TYPE_INDICATOR_FILE].append(find_spec)

  @classmethod
  def BuildFindSpecsFromRegistryArtifact(cls, key_entry, find_specs):
    """Build find specifications from a Windows registry artifact type.

    Args:
      key_entry (str): Current file system key to add.
      find_specs dict[artifacts.artifact_types]:  Dictionary containing
          find_specs.
    """
    separator = '\\'
    for key in path_helper.PathHelper.ExpandRecursiveGlobs(
        key_entry, separator):
      if '%%' in key:
        logging.error(('Unable to expand path filter: "{0:s}"').format(key))
        continue
      find_spec = registry_searcher.FindSpec(key_path_glob=key)
      if artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY not in find_specs:
        find_specs[artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY] = []

      find_specs[artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY].append(
          find_spec)

  @staticmethod
  def _CheckKeyCompatibility(key):
    """Checks if a Windows Registry key is compatible with dfwinreg.

    Args:
      key (str):  String key to to check for dfwinreg compatibility.

    Returns:
      (bool): True if key is compatible or False if not.
    """
    if key.startswith(
        ArtifactDefinitionsFilterHelper._COMPATIBLE_DFWINREG_KEYS):
      return True
    logging.warning('Key "{0:s}", has a prefix that is not supported '
                    'by dfwinreg presently'.format(key))
    return False
