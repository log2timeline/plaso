# -*- coding: utf-8 -*-
"""Trie structure for storing artifact paths."""

import fnmatch
import glob
import os

from plaso.engine import logger
from plaso.engine import path_helper


class TrieNode(object):
  """Represents a node in the Trie.

  Attributes:
    children (dict[str, TrieNode]): Child nodes, keyed by path segment.
    artifacts_names (list[str]): Names of artifacts associated with this node.
    path_separator (str): Path separator used in the Trie.
    is_root (bool): True if this is the root node.
  """

  def __init__(self, path_separator=None, is_root=False):
    """Initializes a trie node object.

    Args:
      path_separator (str): the path separator used in paths stored in
          the Trie, typically '/' or '\'.
      is_root (bool): True if this node is the root node.
    """
    super(TrieNode, self).__init__()
    self.children = {}
    self.artifacts_names = []
    self.path_separator = path_separator
    self.is_root = is_root


class ArtifactsTrie(object):
  """Trie structure for storing artifact paths.

  Attributes:
    root (TrieNode): Root node of the Trie.
    artifacts_paths (dict[str, list[str]]): Artifact paths for glob expansion,
        keyed by artifact name.
  """

  def __init__(self):
    """Initializes an artifact trie object."""
    super(ArtifactsTrie, self).__init__()
    self.root = TrieNode(is_root=True)
    self.artifacts_paths = {}  # Store artifact paths for glob expansion

  def AddPath(self, artifact_name, path, path_separator):
    """Adds a path from an artifact definition to the Trie.

    Args:
      artifact_name (str): name of the artifact.
      path (str): path from the artifact definition.
      path_separator (str): path separator.
    """
    logger.debug(f'Adding path: "{path:s}" to artifact: "{artifact_name:s}"')
    self.artifacts_paths.setdefault(artifact_name, []).append(path)

    # Start at the root
    node = self.root
    # Add a path separator node if this is a new separator
    if path_separator not in node.children:
      node.children[path_separator] = TrieNode(path_separator=path_separator)
    node = node.children[path_separator]
    # Handle handle the case when the input path is equal to the path_separator
    if path == path_separator:
      node.artifacts_names.append(artifact_name)
      return

    path_segments = path.strip(path_separator).split(path_separator)
    for segment in path_segments:
      # Store the path_separator for each node.
      if not hasattr(node, 'path_separator'):
        node.path_separator = path_separator

      if segment not in node.children:
        node.children[segment] = TrieNode(path_separator)
      node = node.children[segment]
    node.artifacts_names.append(artifact_name)

  def GetMatchingArtifacts(self, path, path_separator):
    """Retrieves the artifact names that match the given path.

    Args:
        path (str): path to match against the Trie.
        path_separator (str): path separator.

    Returns:
      list[str]: artifact names that match the path.
    """
    # Start at the root's child that matches the path_separator
    if path_separator not in self.root.children:
      return []

    sub_root_node = self.root.children[path_separator]
    # Handle handle the case when the input path is equal to the path_separator
    if path == path_separator:
      matching_artifacts = set()
      if sub_root_node.artifacts_names:
        matching_artifacts.update(sub_root_node.artifacts_names)
      return list(matching_artifacts)
    path_segments = path.strip(path_separator).split(path_separator)
    matching_artifacts = set()
    # Update self.artifacts_paths before starting the search.
    self.artifacts_paths = self._GetArtifactsPaths(sub_root_node)

    def _search_trie(node, current_path, segments):
      """Searches the trie for paths matching the given path segments.

      Args:
        node (TrieNode): current trie node being traversed.
        current_path (str): path represented by the current node.
        segments (list[str]): remaining path segments to match.
      """
      if node.artifacts_names:
        for artifact_name in node.artifacts_names:
          for artifact_path in self.artifacts_paths.get(artifact_name, []):
            if self._ComparePathIfSanitized(
                    current_path,
                    path_separator,
                    artifact_path,
                    node.path_separator):
              matching_artifacts.add(artifact_name)
            elif glob.has_magic(artifact_path):
              if self._MatchesGlobPattern(
                      artifact_path, current_path, node.path_separator):
                matching_artifacts.add(artifact_name)

      if not segments:
        return

      segment = segments[0]
      remaining_segments = segments[1:]

      # Handle glob characters in the current segment.
      for child_segment, child_node in node.children.items():
        if (
            child_segment == segment or
            # comapring the sanitized version of the path segment stored in
            # the tree to the path segment from to the tool output as it
            # sanitizes path segments before writting data to disk.
            path_helper.PathHelper.SanitizePathSegments(
                [child_segment]).pop() == segment
        ):
          # If the child is an exact match, continue traversal.
          _search_trie(child_node, self._CustomPathJoin(
              path_separator,
              current_path, child_segment), remaining_segments)
        # If the child is a glob, see if it matches.
        elif glob.has_magic(child_segment):
          if self._MatchesGlobPattern(
                  child_segment, segment, child_node.path_separator):
            _search_trie(child_node, self._CustomPathJoin(
                path_separator,
                current_path, segment), remaining_segments)
            _search_trie(
                node,
                self._CustomPathJoin(
                    path_separator,
                    current_path, segment), remaining_segments)

    _search_trie(sub_root_node, '', path_segments)
    return list(matching_artifacts)

  def _ComparePathIfSanitized(
          self,
          current_path,
          path_separator,
          artifact_path,
          atrifact_path_seperator):
    """Compares a current path with an artifact path, handling sanitization.

    This method checks if the current_path matches the artifact_path,
    considering that the artifact_path might have been sanitized.

    Args:
        current_path (str): The current path being checked.
        path_separator (str): Path separator for the current path.
        artifact_path (str): The artifact path to compare against.
        atrifact_path_seperator (str): Path separator for the artifact path.

    Returns:
        bool: True if the current path matches the artifact path (or its
            sanitized version), False otherwise.
    """
    atrifact_path_segments = self._GetNonEmptyPathSegments(
        artifact_path, atrifact_path_seperator)
    return self._GetNonEmptyPathSegments(
        current_path, path_separator) in [
        atrifact_path_segments,
            path_helper.PathHelper.SanitizePathSegments(
                atrifact_path_segments)
    ]

  def _GetNonEmptyPathSegments(self, path, separator):
    """Splits a path into segments and remove non-empty segments.

    Args:
        path (str): The path string to be split.
        separator (str): The path separator.

    Returns:
        list[str]: A list of non-empty path segments.
    """
    return [s for s in path.split(separator) if s]

  def _GetArtifactsPaths(self, node):
    """Retrieves a mapping of artifact names to their paths.

    Args:
      node (TrieNode): current trie node being traversed.

    Returns:
        dict: dictionary mapping artifact names to their paths.
    """
    artifacts_paths = {}

    def _collect_paths(node, current_path, artifacts):
      """Collects paths from the trie.

      Args:
          node (TrieNode): current node.
          current_path (str): path leading to this node.
          artifacts (dict): dictionary to store artifact paths.
      """
      if node.artifacts_names:
        for artifact_name in node.artifacts_names:
          artifacts.setdefault(artifact_name, []).append(current_path)

      for segment, child_node in node.children.items():
        # Ensure the path_separator attribute exists.
        if not hasattr(child_node, 'path_separator'):
          child_node.path_separator = node.path_separator

        # Construct the next path segment.
        if current_path == child_node.path_separator:
          # Means it is the root folder, i.e. `/`
          next_path = current_path + segment
        else:
          next_path = current_path + child_node.path_separator + segment

        _collect_paths(child_node, next_path, artifacts)

    _collect_paths(node, '', artifacts_paths)
    return artifacts_paths

  def _CustomPathJoin(self, separator, current_path, new_segment):
    """Joins path components using a custom separator, replacing os.sep.

    Args:
      separator (str): The custom separator to use.
      current_path (str): The current path.
      new_segment (str): The new segment to add to it.

    Returns:
      str: The joined path with the custom separator.
    """
    current_path = current_path.replace(separator, os.sep)
    joined_path = os.path.join(current_path, new_segment)
    return joined_path.replace(os.sep, separator)

  def _MatchesGlobPattern(self, glob_pattern, path, path_separator):
    """Checks if a path matches a given glob pattern.

    Args:
      glob_pattern: The glob pattern to match against.
      path: The path to check.
      path_separator: The path separator used in the glob pattern.

    Returns:
      True if the path matches the glob pattern, False otherwise.
    """
    # Normalize paths using the appropriate separators
    glob_pattern = glob_pattern.strip(path_separator).split(path_separator)
    path = path.strip(path_separator).split(path_separator)

    i = 0
    j = 0
    while i < len(glob_pattern) and j < len(path):
      if glob_pattern[i] == '**':
        # If ** is the last part, it matches everything remaining
        if i == len(glob_pattern) - 1:
          return True
        i += 1  # Move to the next part after **
        while j < len(path) and not fnmatch.fnmatch(path[j], glob_pattern[i]):
          j += 1  # Keep advancing in the path until the next part matches
      elif not fnmatch.fnmatch(path[j], glob_pattern[i]):
        return False  # Mismatch
      else:
        i += 1
        j += 1

    return i == len(glob_pattern) and j == len(path)
