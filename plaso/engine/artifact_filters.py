# -*- coding: utf-8 -*-
"""Helper to create filters based on forensic artifact definitions."""

from __future__ import unicode_literals

import logging
import re

from artifacts import definitions as artifact_types

from dfvfs.helpers import file_system_searcher
from dfwinreg import registry_searcher

from plaso.engine import path_helper

class ArtifactDefinitionsFilterHelper(object):
  """Helper to create filters based on artifact defintions.

  Builds extraction and parsing filters from forensic artifact definitions.

  For more information about Forensic Artifacts see:
  https://github.com/ForensicArtifacts/artifacts/blob/master/docs/Artifacts%20definition%20format%20and%20style%20guide.asciidoc
  """

  ARTIFACT_FILTERS = 'ARTIFACT_FILTERS'
  COMPATIBLE_DFWINREG_KEYS = frozenset([
      'HKEY_LOCAL_MACHINE',
      'HKEY_LOCAL_MACHINE\\SYSTEM',
      'HKEY_LOCAL_MACHINE\\SOFTWARE',
      'HKEY_LOCAL_MACHINE\\SAM',
      'HKEY_LOCAL_MACHINE\\SECURITY'])
  STANDARD_OS_FILTERS = frozenset([
      'windows',
      'linux',
      'darwin'])
  RECURSIVE_GLOB_LIMIT = 10

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
    """Build find specification from a forensic artifact definitions.

    Args:
      environment_variables (Optional[list[EnvironmentVariableArtifact]]):
          environment variables.
    """
    find_specs = {}

    artifact_defintions = []
    # Check if single operating system type has been provided, in that case
    # process all artifact types for that OS.
    if (len(self._artifacts) == 1 and
            self._artifacts[0] in self.STANDARD_OS_FILTERS):
      for definition in self._artifacts_registry.GetDefinitions():
        if self._filters[0].lower() in (
            os.lower() for os in definition.supported_os):
          artifact_defintions.append(definition)
    else:
      for artifact_filter in self._artifacts:
        if self._artifacts_registry.GetDefinitionByName(artifact_filter):
          artifact_defintions.append(
            self._artifacts_registry.GetDefinitionByName(artifact_filter))

    for definition in artifact_defintions:
      for source in definition.sources:
        if source.type_indicator == artifact_types.TYPE_INDICATOR_FILE:
          for path_entry in source.paths:
            self.BuildFindSpecsFromFileArtifact(
              path_entry, source.separator, environment_variables, find_specs)
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
          logging.warning(('Unable to handle Registry Value, extracting '
                           'key only: {0:s} ').format(source.key_value_pairs))

          for key_pair in source.key_value_pairs:
            keys = set()
            keys.add(key_pair.get('key'))
            for key_entry in keys:
              if self._CheckKeyCompatibility(key_entry):
                self.BuildFindSpecsFromRegistryArtifact(
                  key_entry, find_specs)
        else:
          logging.warning(('Unable to handle artifact, plaso does not '
                           'support: {0:s} ').format(source.type_indicator))

    self._knowledge_base.SetValue(self.ARTIFACT_FILTERS, find_specs)

  def BuildFindSpecsFromFileArtifact(
      self, path_entry, separator, environment_variables, find_specs):
    """Build find specification from a FILE artifact type.

    Args:
      path_entry (str):  Current file system path to add.
          environment variables.
      separator (str): File system path separator.
      environment_variables list(str):  Environment variable attributes used to
          dynamically populate environment variables in key.
      find_specs dict[artifacts.artifact_types]:  Dictionary containing
          find_specs.
    """
    for glob_path in self._ExpandRecursiveGlobs(path_entry):
      for path in path_helper.PathHelper.ExpandUserHomeDirPath(
          glob_path, self._knowledge_base.user_accounts):
        if '%' in path:
          path = path_helper.PathHelper.ExpandWindowsPath(
              path, environment_variables)

        if not path.startswith('/') and not path.startswith('\\'):
          logging.warning((
              'The path filter must be defined as an absolute path: '
              '{0:s}').format(path))
          continue

        # Convert the path filters into a list of path segments and
        # strip the root path segment.
        path_segments = path.split(separator)

        # If the source didn't specify a separator, '/' is returned by
        # default from ForensicArtifacts, this is sometimes wrong.  Thus,
        # need to check if '\' characters are still present and split on those.
        if len(path_segments) == 1 and '\\' in path_segments[0]:
          logging.warning('Potentially bad separator = {0:s} , trying \'\\\''
                          .format(separator))
          path_segments = path.split('\\')
        path_segments.pop(0)

        if not path_segments[-1]:
          logging.warning(
              'Empty last path segment in path filter: {0:s}'.format(path))
          path_segments.pop(-1)

        try:
          find_spec = file_system_searcher.FindSpec(
              location_glob=path_segments, case_sensitive=False)
        except ValueError as exception:
          logging.error((
              'Unable to build find spec for path: {0:s} with error: {1!s}'
          ).format(path, exception))
          continue
        if artifact_types.TYPE_INDICATOR_FILE not in find_specs:
          find_specs[artifact_types.TYPE_INDICATOR_FILE] = []
        find_specs[artifact_types.TYPE_INDICATOR_FILE].append(
            find_spec)

  def BuildFindSpecsFromRegistryArtifact(
      self, key_entry, find_specs):
    """Build find specification from a Windows registry artifact type.

    Args:
      key_entry (str):  Current file system key to add.
      find_specs dict[artifacts.artifact_types]:  Dictionary containing
          find_specs.
    """
    for key in self._ExpandRecursiveGlobs(key_entry):
      if '%%' in key:
        logging.error((
            'Unable to expand path filter: {0:s}').format(key))
        continue
      find_spec = registry_searcher.FindSpec(key_path_glob=key)
      if artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY not in find_specs:
        find_specs[artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY] = []

      find_specs[artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY].append(
          find_spec)

  def _CheckKeyCompatibility(self, key):
    """Check if a registry key is compatible with dfwinreg.

    Args:
      key (str):  String key to to check for dfwinreg compatibility.

    Returns:
      (bool): Boolean whether key is compatible or not.
    """
    key_path_prefix = key.split('\\')[0]
    if key_path_prefix.upper() in self.COMPATIBLE_DFWINREG_KEYS:
      return True
    logging.warning('Key {0:s}, has a prefix {1:s} that is not supported '
                    'by dfwinreg presently'.format(key, key_path_prefix))
    return False

  def _ExpandRecursiveGlobs(self, path):
    """Expand recursive like globs present in an artifact path.

    If a path ends in '**', with up two optional digits such as '**10',
    the '**' will match all files and zero or more directories and
    subdirectories from the specified path recursively. The optional digits
    provide the depth to which the recursion should continue.  By default
    recursion depth is 10 directories.  If the pattern is followed by a ‘/’
    or '\', only directories and subdirectories match.

    Args:
      path (str):  String path to be expanded.

    Returns:
      list[str]: String path expanded for each glob.
    """

    match = re.search(r'(.*)?(\\|/)\*\*(\d{1,2})?(\\|/)?$', path)
    if match:
      skip_first = False
      if match.group(4):
        skip_first = True
      if match.group(3):
        iterations = match.group(3)
      else:
        iterations = self.RECURSIVE_GLOB_LIMIT
        logging.warning('Path {0:s} contains fully recursive glob, limiting '
                        'to ten levels'.format(path))
      paths = self._BuildRecursivePaths(match.group(1), iterations, skip_first)
      return paths
    else:
      return [path]

  def _BuildRecursivePaths(self, path, count, skip_first):
    """Append wildcard entries to end of path.

    Args:
      path (str):  Path to append wildcards to.

    Returns:
      path list[str]: Paths expanded with wildcards.
    """
    paths = []
    if '\\' in path:
      replacement = '\\*'
    else:
      replacement = '/*'

    for iteration in range(count):
      if skip_first and iteration == 0:
        continue
      else:
        path += replacement
        paths.append(path)
      iteration += 1

    return paths
