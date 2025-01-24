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
    artifacts_names (list[str]): Names of artifacts associated with this node.
    children (dict[str, TrieNode]): Child nodes, keyed by path segment.
    is_root (bool): True if this is the root node.
    path_separator (str): Path separator used in the Trie, default is '/'.
  """

  def __init__(self, path_separator='/', is_root=False):
    """Initializes a trie node object.

    Args:
      path_separator (Optional[str]): the path separator used in paths stored
          in the Trie, default is '/'.
      is_root (bool): True if this node is the root node.
    """
    super(TrieNode, self).__init__()
    self.artifacts_names = []
    self.children = {}
    self.is_root = is_root
    self.path_separator = path_separator


class ArtifactsTrie(object):
  """Trie structure for storing artifact paths.

  Attributes:
    artifacts_paths (dict[str, list[str]]): Artifact paths for glob expansion,
        keyed by artifact name.
    root (TrieNode): Root node of the Trie.
  """

  def __init__(self):
    """Initializes an artifact trie object."""
    super(ArtifactsTrie, self).__init__()
    self.artifacts_paths = {}
    self.root = TrieNode(is_root=True)

  def AddPath(self, artifact_name, path, path_separator):
    """Adds a path from an artifact definition to the Trie.

    Args:
      artifact_name (str): name of the artifact.
      path (str): path from the artifact definition.
      path_separator (str): path separator.
    """
    logger.debug(f'Adding path: "{path:s}" to artifact: "{artifact_name:s}"')
    path_list = self.artifacts_paths.setdefault(artifact_name, [])
    path_list.append(path)

    current_node = self.root

    # Add a path separator node if this is a new separator.
    if path_separator not in current_node.children:
      current_node.children[path_separator] = TrieNode(
          path_separator=path_separator)
    current_node = current_node.children[path_separator]

    # Handle the case when the input path is equal to the path_separator.
    if path == path_separator:
      current_node.artifacts_names.append(artifact_name)
      return

    path_segments = path.strip(path_separator).split(path_separator)
    for path_segment in path_segments:
      # Store the path_separator for each node.
      if not hasattr(current_node, 'path_separator'):
        current_node.path_separator = path_separator

      if path_segment not in current_node.children:
        current_node.children[path_segment] = TrieNode(path_separator)
      current_node = current_node.children[path_segment]
    current_node.artifacts_names.append(artifact_name)

  def GetMatchingArtifacts(self, path, path_separator):
    """Retrieves the artifact names that match the given path.

    Args:
        path (str): path to match against the Trie.
        path_separator (str): path separator.

    Returns:
      list[str]: artifact names that match the path.
    """
    # Start at the root's child that matches the path_separator.
    if path_separator not in self.root.children:
      return []

    sub_root_node = self.root.children[path_separator]

    # Handle the case when the input path is equal to the path_separator.
    if path == path_separator:
      matching_artifacts = set()
      if sub_root_node.artifacts_names:
        matching_artifacts.update(sub_root_node.artifacts_names)
      return list(matching_artifacts)
    path_segments = path.strip(path_separator).split(path_separator)
    matching_artifacts = set()
    # Update self.artifacts_paths before starting the search.
    self.artifacts_paths = self._GetArtifactsPaths(sub_root_node)

    self._SearchTrie(
      sub_root_node, '', path_segments, path_separator, matching_artifacts)
    return list(matching_artifacts)

  def _SearchTrie(
      self,node, current_path, segments, path_separator, matching_artifacts):
    """Searches the trie for paths matching the given path segments.

    Args:
      node (TrieNode): current trie node being traversed.
      current_path (str): path represented by the current node.
      segments (list[str]): remaining path segments to match.
      path_separator (str): path separator.
      matching_artifacts (set[str]): Set to store matching artifact names.
    """
    if node.artifacts_names:
      for artifact_name in node.artifacts_names:
        for artifact_path in self.artifacts_paths.get(artifact_name, []):
          if self._ComparePathIfSanitized(
              current_path, path_separator, artifact_path,
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
      # Compare the sanitized version of the path segment stored in
      # the tree to the path segment from to the tool output as it
      # sanitizes path segments before writing data to disk.
      sanitized_child_segment = path_helper.PathHelper.SanitizePathSegments(
          [child_segment]).pop()

      # If the child is an exact match, continue traversal.
      if segment in (child_segment, sanitized_child_segment):
        custom_path = _CustomPathJoin(
            path_separator, current_path, child_segment)
        self._SearchTrie(
            child_node, custom_path, remaining_segments, path_separator,
            matching_artifacts)
        
      # If the child is a glob, see if it matches.
      elif glob.has_magic(child_segment):
        if self._MatchesGlobPattern(
                child_segment, segment, child_node.path_separator):
          custom_path = _CustomPathJoin(
              path_separator, current_path, segment)
          self._SearchTrie(
              child_node, custom_path, remaining_segments, path_separator,
              matching_artifacts)
          self._SearchTrie(
              node, custom_path, remaining_segments, path_separator,
              matching_artifacts)

  def _ComparePathIfSanitized(
      self, current_path, path_separator, artifact_path,
      artifact_path_seperator):
    """Compares a current path with an artifact path, handling sanitization.

    This method checks if the current_path matches the artifact_path,
    considering that the artifact_path might have been sanitized.

    Args:
      current_path (str): The current path being checked.
      path_separator (str): Path separator for the current path.
      artifact_path (str): The artifact path to compare against.
      artifact_path_seperator (str): Path separator for the artifact path.

    Returns:
      bool: True if the current path matches the artifact path or its
          sanitized version, False otherwise.
    """
    artifact_path_segments = self._GetNonEmptyPathSegments(
        artifact_path, artifact_path_seperator)
    sanitized_path_segments = path_helper.PathHelper.SanitizePathSegments(
        artifact_path_segments)
    return self._GetNonEmptyPathSegments(current_path, path_separator) in [
        artifact_path_segments, sanitized_path_segments]

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
          path_list = artifacts.setdefault(artifact_name, [])
          path_list.append(current_path)

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

    glob_index = 0
    path_index = 0
    while glob_index < len(glob_pattern) and path_index < len(path):
      if glob_pattern[glob_index] == '**':
        # If ** is the last part, it matches everything remaining
        if glob_index == len(glob_pattern) - 1:
          return True
        # Move to the next part after **
        glob_index += 1
        # Keep advancing in the path until the next part matches
        while path_index < len(path) and not fnmatch.fnmatch(
          path[path_index], glob_pattern[glob_index]):
          path_index += 1
      elif not fnmatch.fnmatch(path[path_index], glob_pattern[glob_index]):
        # Mismatch
        return False
      else:
        glob_index += 1
        path_index += 1

    return glob_index == len(glob_pattern) and path_index == len(path)
