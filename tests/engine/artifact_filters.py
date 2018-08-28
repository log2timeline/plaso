#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the artifacts file filter functions."""

from __future__ import unicode_literals

import unittest

from artifacts import definitions as artifact_types
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher as dfwinreg_registry_searcher

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import artifacts
from plaso.engine import artifact_filters
from plaso.engine import knowledge_base as knowledge_base_engine
from plaso.lib import py2to3
from plaso.parsers import winreg as windows_registry_parser

from tests import test_lib as shared_test_lib


class ArtifactDefinitionsFilterHelperTest(shared_test_lib.BaseTestCase):
  """Tests for artifact definitions filter helper."""

  # pylint: disable=protected-access

  def _CreateTestArtifactDefinitionsFilterHelper(
      self, artifact_definitions, knowledge_base):
    """Creates an artifact definitions filter helper for testing.

    Args:
      artifact_definitions (list[str]): artifact definition names to filter.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for filtering.

    Returns:
      ArtifactDefinitionsFilterHelper: artifact definitions filter helper.
    """
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    registry.ReadFromDirectory(reader, test_artifacts_path)

    return artifact_filters.ArtifactDefinitionsFilterHelper(
        registry, artifact_definitions, knowledge_base)

  @shared_test_lib.skipUnlessHasTestFile(['artifacts'])
  @shared_test_lib.skipUnlessHasTestFile(['System.evtx'])
  @shared_test_lib.skipUnlessHasTestFile(['testdir', 'filter_1.txt'])
  @shared_test_lib.skipUnlessHasTestFile(['testdir', 'filter_3.txt'])
  def testBuildFindSpecsWithFileSystem(self):
    """Tests the BuildFindSpecs function for file type artifacts."""
    knowledge_base = knowledge_base_engine.KnowledgeBase()

    testuser1 = artifacts.UserAccountArtifact(
        identifier='1000',
        user_directory='C:\\\\Users\\\\testuser1',
        username='testuser1')
    knowledge_base.AddUserAccount(testuser1)

    testuser2 = artifacts.UserAccountArtifact(
        identifier='1001',
        user_directory='C:\\\\Users\\\\testuser2',
        username='testuser2')
    knowledge_base.AddUserAccount(testuser2)

    test_filter_file = self._CreateTestArtifactDefinitionsFilterHelper(
        ['TestFiles', 'TestFiles2'], knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemDrive', value='C:')

    test_filter_file.BuildFindSpecs(
        environment_variables=[environment_variable])
    find_specs_per_source_type = knowledge_base.GetValue(
        test_filter_file.KNOWLEDGE_BASE_VALUE)
    find_specs = find_specs_per_source_type.get(
        artifact_types.TYPE_INDICATOR_FILE, [])

    # Should build 15 FindSpec entries.
    self.assertEqual(len(find_specs), 15)

    # Last find_spec should contain the testuser2 profile path.
    location_segments = sorted([
        find_spec._location_segments for find_spec in find_specs])
    path_segments = [
        'Users', 'testuser2', 'Documents', 'WindowsPowerShell', 'profile\\.ps1']
    self.assertEqual(location_segments[2], path_segments)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(find_specs=find_specs)
    self.assertIsNotNone(path_spec_generator)

    path_specs = list(path_spec_generator)

    # Two evtx, one symbolic link to evtx, one AUTHORS, two filter_*.txt files,
    # total 6 path specifications.
    self.assertEqual(len(path_specs), 6)

    file_system.Close()

  @shared_test_lib.skipUnlessHasTestFile(['artifacts'])
  @shared_test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testBuildFindSpecsWithRegistry(self):
    """Tests the BuildFindSpecs function on Windows Registry artifacts."""
    knowledge_base = knowledge_base_engine.KnowledgeBase()
    test_filter_file = self._CreateTestArtifactDefinitionsFilterHelper(
        ['TestRegistry'], knowledge_base)

    test_filter_file.BuildFindSpecs(environment_variables=None)
    find_specs_per_source_type = knowledge_base.GetValue(
        test_filter_file.KNOWLEDGE_BASE_VALUE)
    find_specs = find_specs_per_source_type.get(
        artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY, [])

    self.assertEqual(len(find_specs), 1)

    win_registry_reader = (
        windows_registry_parser.FileObjectWinRegistryFileReader())

    file_entry = self._GetTestFileEntry(['SYSTEM'])
    file_object = file_entry.GetFileObject()

    registry_file = win_registry_reader.Open(file_object)

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    registry_file.SetKeyPathPrefix(key_path_prefix)
    win_registry.MapFile(key_path_prefix, registry_file)

    searcher = dfwinreg_registry_searcher.WinRegistrySearcher(win_registry)
    key_paths = list(searcher.Find(find_specs=find_specs))

    self.assertIsNotNone(key_paths)

    # Three key paths found.
    self.assertEqual(len(key_paths), 3)

  def testCheckKeyCompatibility(self):
    """Tests the CheckKeyCompatibility function"""
    knowledge_base = knowledge_base_engine.KnowledgeBase()
    test_filter_file = self._CreateTestArtifactDefinitionsFilterHelper(
        [], knowledge_base)

    # Compatible Key.
    key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control'
    compatible_key = test_filter_file.CheckKeyCompatibility(key_path)
    self.assertTrue(compatible_key)

    # NOT a Compatible Key.
    key_path = 'HKEY_USERS\\S-1-5-18'
    compatible_key = test_filter_file.CheckKeyCompatibility(key_path)
    self.assertFalse(compatible_key)

  def testBuildFindSpecsFromFileArtifact(self):
    """Tests the BuildFindSpecsFromFileArtifact function for file artifacts."""
    knowledge_base = knowledge_base_engine.KnowledgeBase()
    test_filter_file = self._CreateTestArtifactDefinitionsFilterHelper(
        [], knowledge_base)

    separator = '\\'
    user_accounts = []

    # Test expansion of environment variables.
    path_entry = '%%environ_systemroot%%\\test_data\\*.evtx'
    environment_variable = [artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')]

    find_specs = test_filter_file.BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts)

    # Should build 1 find_spec.
    self.assertEqual(len(find_specs), 1)

    # Location segments should be equivalent to \Windows\test_data\*.evtx.
    if py2to3.PY_3:
      # Underscores are not escaped in regular expressions in supported versions
      # of Python 3. See https://bugs.python.org/issue2650.
      path_segments = ['Windows', 'test_data', '.*\\.evtx']
    else:
      path_segments = ['Windows', 'test\\_data', '.*\\.evtx']

    self.assertEqual(find_specs[0]._location_segments, path_segments)

    # Test expansion of globs.
    path_entry = '\\test_data\\**'
    find_specs = test_filter_file.BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts)

    # Glob expansion should by default recurse ten levels.
    self.assertEqual(len(find_specs), 10)

    # Last entry in find_specs list should be 10 levels of depth.
    if py2to3.PY_3:
      # Underscores are not escaped in regular expressions in supported versions
      # of Python 3. See https://bugs.python.org/issue2650
      path_segments = ['test_data']
    else:
      path_segments = ['test\\_data']

    path_segments.extend([
        '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*'])

    self.assertEqual(find_specs[9]._location_segments, path_segments)

    # Test expansion of user home directories
    separator = '/'
    testuser1 = artifacts.UserAccountArtifact(
        user_directory='/homes/testuser1', username='testuser1')
    testuser2 = artifacts.UserAccountArtifact(
        user_directory='/home/testuser2', username='testuser2')
    user_accounts = [testuser1, testuser2]
    path_entry = '%%users.homedir%%/.thumbnails/**3'

    find_specs = test_filter_file.BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts)

    # Six total find specs should be created for testuser1 and testuser2.
    self.assertEqual(len(find_specs), 6)

    # Last entry in find_specs list should be testuser2 with a depth of 3
    path_segments = ['home', 'testuser2', '\\.thumbnails', '.*', '.*', '.*']
    self.assertEqual(find_specs[5]._location_segments, path_segments)

    # Test Windows path with profile directories and globs with a depth of 4.
    separator = '\\'
    testuser1 = artifacts.UserAccountArtifact(
        user_directory='\\Users\\\\testuser1', username='testuser1')
    testuser2 = artifacts.UserAccountArtifact(
        user_directory='\\Users\\\\testuser2', username='testuser2')
    user_accounts = [testuser1, testuser2]
    path_entry = '%%users.homedir%%\\AppData\\**4'

    find_specs = test_filter_file.BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts)

    # Eight find specs should be created for testuser1 and testuser2.
    self.assertEqual(len(find_specs), 8)

    # Last entry in find_specs list should be testuser2, with a depth of 4.
    path_segments = ['Users', 'testuser2', 'AppData', '.*', '.*', '.*', '.*']
    self.assertEqual(find_specs[7]._location_segments, path_segments)


if __name__ == '__main__':
  unittest.main()
