# -*- coding: utf-8 -*-
"""Tests for the artifacts trie."""

import unittest

from plaso.engine import artifacts_trie


class TrieNodeTest(unittest.TestCase):
  """Tests for the TrieNode object."""

  def test_initialization(self):
    """Test that the node can be initialized."""
    node = artifacts_trie.TrieNode()
    self.assertIsNotNone(node)
    self.assertEqual(node.children, {})
    self.assertEqual(node.artifacts_names, [])
    self.assertIsNone(node.path_separator)

  # You can add more tests for TrieNode if needed, but it's a simple class.


class ArtifactsTrieTest(unittest.TestCase):
  """Tests for the artifactsTrie object."""

  def setUp(self):
    """Setup a trie for testing."""
    self.trie = artifacts_trie.ArtifactsTrie()

  def test_add_path(self):
    """Tests the AddPath function."""
    self.trie.AddPath('artifact1', '/path/to/file.txt', '/')
    self.trie.AddPath('artifact2', '/path/to/another.txt', '/')

    root = self.trie.root
    self.assertIn('/', root.children)
    self.assertIn('path', root.children['/'].children)
    self.assertIn('to', root.children['/'].children['path'].children)
    self.assertIn(
        'file.txt', root.children['/'].children['path'].children['to'].children)
    self.assertIn(
        'another.txt',
        root.children['/'].children['path'].children['to'].children
    )
    self.assertEqual(
        root.children['/']
        .children['path']
        .children['to']
        .children['file.txt']
        .artifacts_names,
        ['artifact1'],
    )
    self.assertEqual(
        root.children['/']
        .children['path']
        .children['to']
        .children['another.txt']
        .artifacts_names,
        ['artifact2']
    )

  def test_add_path_with_glob(self):
    """Tests the AddPath function with glob patterns."""
    self.trie.AddPath('artifact1', '/path/to/*.txt', '/')
    self.trie.AddPath('artifact2', '/path/to/dir**', '/')

    root = self.trie.root
    self.assertIn('/', root.children)
    self.assertIn('path', root.children['/'].children)
    self.assertIn('to', root.children['/'].children['path'].children)
    self.assertIn(
        '*.txt', root.children['/'].children['path'].children['to'].children)
    self.assertIn(
        'dir**', root.children['/'].children['path'].children['to'].children)
    self.assertEqual(
        root.children['/']
        .children['path']
        .children['to']
        .children['*.txt']
        .artifacts_names,
        ['artifact1']
    )
    self.assertEqual(
        root.children['/']
        .children['path']
        .children['to']
        .children['dir**']
        .artifacts_names,
        ['artifact2']
    )

  def test_get_matching_artifacts_no_glob(self):
    """Tests GetMatchingArtifacts without glob."""
    self.trie.AddPath('artifact1', '/path/to/file.txt', '/')
    self.trie.AddPath('artifact2', '/path/to/another.txt', '/')

    matches = self.trie.GetMatchingArtifacts('/path/to/file.txt', '/')
    self.assertIn('artifact1', matches)
    self.assertNotIn('artifact2', matches)

  def test_get_matching_artifacts_with_glob(self):
    """Tests GetMatchingArtifacts with glob patterns."""
    self.trie.AddPath('artifact1', '/path/to/*.txt', '/')
    self.trie.AddPath('artifact2', '/path/**/file.txt', '/')
    # The trie structure will have these paths and children
    # root
    #  |
    #  /
    #  |
    #  path
    #   |
    #  to, **
    #   |   |
    #  *.txt  file.txt

    matches = self.trie.GetMatchingArtifacts('/path/to/file.txt', '/')
    self.assertIn('artifact1', matches)
    self.assertIn('artifact2', matches)

    matches = self.trie.GetMatchingArtifacts('/path/to/dir/file.txt', '/')
    self.assertIn('artifact2', matches)
    self.assertNotIn('artifact1', matches)

  def test_get_matching_artifacts_with_multiple_globs(self):
    """Tests GetMatchingArtifacts with multiple consecutive glob patterns."""
    self.trie.AddPath('artifact1', '/**/**/file.txt', '/')
    self.trie.AddPath('artifact2', '/**/**/another.txt', '/')

    # The trie structure will have these paths and children
    # root
    #  |
    #  /
    #  |
    #  **
    #   |
    #  **, file.txt, another.txt

    matches = self.trie.GetMatchingArtifacts(
        '/path/to/dir/subdir/file.txt', '/')
    self.assertIn('artifact1', matches)
    self.assertNotIn('artifact2', matches)

    matches = self.trie.GetMatchingArtifacts(
        '/path/to/dir/subdir/another.txt', '/')
    self.assertIn('artifact2', matches)
    self.assertNotIn('artifact1', matches)

  def test_get_matching_artifacts_single_asterisk(self):
    """Tests GetMatchingArtifacts with single asterisk glob patterns."""
    self.trie.AddPath('artifact1', '/path/to/*/file.txt', '/')
    self.trie.AddPath('artifact2', '/path/*/data/*.txt', '/')
    self.trie.AddPath(
        'artifact3', '/home/*/.jupyter/jupyter_notebook_config.py', '/')

    matches = self.trie.GetMatchingArtifacts('/path/to/dir/file.txt', '/')
    self.assertIn('artifact1', matches)
    self.assertNotIn('artifact2', matches)

    matches = self.trie.GetMatchingArtifacts(
        '/path/dir/data/test.txt', '/')
    self.assertNotIn('artifact1', matches)
    self.assertIn('artifact2', matches)

    matches = self.trie.GetMatchingArtifacts(
        '/home/dummyuser/.jupyter/jupyter_notebook_config.py', '/')
    self.assertNotIn('artifact1', matches)
    self.assertNotIn('artifact2', matches)
    self.assertIn('artifact3', matches)

  def test_get_matching_artifacts_windows_paths(self):
    """Tests GetMatchingArtifacts with Windows paths."""
    self.trie.AddPath('artifact1', '\\Windows\\System32\\*.dll', '\\')
    self.trie.AddPath('artifact2', '\\Users\\**\\AppData\\*', '\\')

    matches = self.trie.GetMatchingArtifacts(
        '\\Windows\\System32\\kernel32.dll', '\\')
    self.assertIn('artifact1', matches)
    self.assertNotIn('artifact2', matches)

    matches = self.trie.GetMatchingArtifacts(
        '\\Users\\test\\AppData\\Local', '\\')
    self.assertIn('artifact2', matches)
    self.assertNotIn('artifact1', matches)

  def test_get_matching_artifacts_negative_cases(self):
    """Tests GetMatchingArtifacts with non-matching cases."""
    self.trie.AddPath('artifact1', '/path/to/file.txt', '/')
    self.trie.AddPath('artifact2', '/path/to/*.txt', '/')
    self.trie.AddPath('artifact3', '/path/**/file.txt', '/')

    matches = self.trie.GetMatchingArtifacts('/path/to/other.txt', '/')
    self.assertNotIn('artifact1', matches)
    self.assertNotIn('artifact3', matches)

    matches = self.trie.GetMatchingArtifacts('/path/dir/file.txt', '/')
    self.assertNotIn('artifact1', matches)
    self.assertNotIn('artifact2', matches)

    matches = self.trie.GetMatchingArtifacts('/path/to/dir/test/fi*.txt', '/')
    self.assertNotIn('artifact1', matches)
    self.assertNotIn('artifact2', matches)

  def test_add_path_with_mixed_separators(self):
    """Tests the AddPath function with mixed path separators."""
    self.trie.AddPath('artifact1', '/mixed/path/style', '/')
    self.trie.AddPath('artifact2', '\\another\\mixed\\style', '\\')

    root = self.trie.root
    self.assertIn('/', root.children)
    self.assertIn('mixed', root.children['/'].children)

    self.assertIn('\\', root.children)
    self.assertIn('another', root.children['\\'].children)

  def test_get_matching_artifacts_mixed_separators(self):
    """Tests GetMatchingArtifacts with mixed path separators."""
    self.trie.AddPath('artifact1', '/mixed/path/style', '/')
    self.trie.AddPath('artifact2', '\\another\\mixed\\style', '\\')

    matches = self.trie.GetMatchingArtifacts('/mixed/path/style', '/')
    self.assertIn('artifact1', matches)

    matches = self.trie.GetMatchingArtifacts('\\another\\mixed\\style', '\\')
    self.assertIn('artifact2', matches)

  def test_get_matching_artifacts_same_path_different_artifacts(self):
    """Tests GetMatchingArtifacts with same path for different artifacts."""
    self.trie.AddPath('artifact1', '/same/path/file.txt', '/')
    self.trie.AddPath('artifact2', '/same/path/file.txt', '/')

    matches = self.trie.GetMatchingArtifacts('/same/path/file.txt', '/')
    self.assertIn('artifact1', matches)
    self.assertIn('artifact2', matches)

  def test_get_matching_artifacts_empty_path(self):
    """Tests GetMatchingArtifacts with an empty path."""
    self.trie.AddPath('artifact1', '/path/to/file.txt', '/')

    matches = self.trie.GetMatchingArtifacts('', '/')
    self.assertEqual(len(matches), 0)

  def test_get_matching_artifacts_root_path(self):
    """Tests GetMatchingArtifacts with root path."""
    self.trie.AddPath('artifact1', '/', '/')

    matches = self.trie.GetMatchingArtifacts('/', '/')
    self.assertIn('artifact1', matches)

  def test_get_matching_artifacts_nonexistent_path(self):
    """Tests GetMatchingArtifacts with a nonexistent path."""
    self.trie.AddPath('artifact1', '/path/to/file.txt', '/')

    matches = self.trie.GetMatchingArtifacts('/nonexistent/path', '/')
    self.assertEqual(len(matches), 0)

  def test_get_matching_artifacts_case_sensitivity(self):
    """Tests GetMatchingArtifacts with different case sensitivity."""
    self.trie.AddPath('artifact1', '/path/to/file.txt', '/')

    matches = self.trie.GetMatchingArtifacts('/Path/To/File.TXT', '/')
    self.assertNotIn('artifact1', matches)

  def test_get_matching_artifacts_special_characters(self):
    """Tests GetMatchingArtifacts with special characters in path."""
    self.trie.AddPath('artifact1', '/path/to/file[0-9].txt', '/')

    matches = self.trie.GetMatchingArtifacts('/path/to/file1.txt', '/')
    self.assertIn('artifact1', matches)

    matches = self.trie.GetMatchingArtifacts('/path/to/file.txt', '/')
    self.assertNotIn('artifact1', matches)


if __name__ == '__main__':
  unittest.main()
