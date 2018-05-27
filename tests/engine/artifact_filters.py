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
from plaso.parsers import winreg as windows_registry_parser

from tests import test_lib as shared_test_lib


class BuildFindSpecsFromFileTest(shared_test_lib.BaseTestCase):
  """Tests for the BuildFindSpecsFromFile function."""

  # pylint: disable=protected-access

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
    testuser2 = artifacts.UserAccountArtifact(
        identifier='1001',
        user_directory='C:\\\\Users\\\\testuser2',
        username='testuser2')
    knowledge_base.AddUserAccount(testuser1)
    knowledge_base.AddUserAccount(testuser2)

    artifact_definitions = ['TestFiles', 'TestFiles2']
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    registry.ReadFromDirectory(reader, self._GetTestFilePath(['artifacts']))

    test_filter_file = artifact_filters.ArtifactDefinitionsFilterHelper(
        registry, artifact_definitions, knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemDrive', value='C:')

    test_filter_file.BuildFindSpecs(
        environment_variables=[environment_variable])
    find_specs = knowledge_base.GetValue(
        artifact_filters.ArtifactDefinitionsFilterHelper.ARTIFACT_FILTERS)

    # Should build 15 FindSpec entries.
    self.assertEqual(len(find_specs[artifact_types.TYPE_INDICATOR_FILE]), 15)

    # Last entry in find_specs list should be testuser2.
    path_segments = ['Users', 'testuser2', 'Documents', 'WindowsPowerShell',
                     'profile\\.ps1']
    self.assertEqual(
         find_specs[artifact_types.TYPE_INDICATOR_FILE][2]._location_segments,
         path_segments)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(
        find_specs=find_specs[artifact_types.TYPE_INDICATOR_FILE])
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

    artifact_definitions = ['TestRegistry']
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    registry.ReadFromDirectory(reader, self._GetTestFilePath(['artifacts']))

    test_filter_file = artifact_filters.ArtifactDefinitionsFilterHelper(
        registry, artifact_definitions, knowledge_base)

    test_filter_file.BuildFindSpecs(environment_variables=None)
    find_specs = knowledge_base.GetValue(
        artifact_filters.ArtifactDefinitionsFilterHelper.ARTIFACT_FILTERS)

    self.assertEqual(
        len(find_specs[artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY]), 1)

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
    key_paths = list(searcher.Find(find_specs=find_specs[
        artifact_types.TYPE_INDICATOR_WINDOWS_REGISTRY_KEY]))

    self.assertIsNotNone(key_paths)

    # Three key paths found.
    self.assertEqual(len(key_paths), 3)

  def test_CheckKeyCompatibility(self):
    """Tests the _CheckKeyCompatibility function"""

    # Compatible Key.
    key = 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control'
    compatible_key = (
        artifact_filters.ArtifactDefinitionsFilterHelper._CheckKeyCompatibility(
            key))
    self.assertTrue(compatible_key)

    # NOT a Compatible Key.
    key = 'HKEY_USERS\\S-1-5-18'
    compatible_key = (
        artifact_filters.ArtifactDefinitionsFilterHelper._CheckKeyCompatibility(
            key))
    self.assertFalse(compatible_key)


  def testBuildFindSpecsFromFileArtifact(self):
    """Tests the BuildFindSpecsFromFileArtifact function for file artifacts."""
    find_specs = {}
    separator = '\\'
    user_accounts = []

    # Test expansion of environment variables.
    path_entry = '%%environ_systemroot%%\\test_data\\*.evtx'
    environment_variable = [artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')]

    (artifact_filters.ArtifactDefinitionsFilterHelper.
    BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts,
        find_specs))

    # Should build 1 find_spec.
    self.assertEqual(len(find_specs[artifact_types.TYPE_INDICATOR_FILE]), 1)

    # Location segments should be equivalent to \Windows\test_data\*.evtx.
    path_segments = ['Windows', 'test\\_data', '.*\\.evtx']
    self.assertEqual(
        find_specs[artifact_types.TYPE_INDICATOR_FILE][0]._location_segments,
        path_segments)


    # Test expansion of globs.
    find_specs = {}
    path_entry = '\\test_data\\**'
    (artifact_filters.ArtifactDefinitionsFilterHelper.
    BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts,
        find_specs))

    # Glob expansion should by default recurse ten levels.
    self.assertEqual(len(find_specs[artifact_types.TYPE_INDICATOR_FILE]), 10)

    # Last entry in find_specs list should be 10 levels of depth.
    path_segments = [
        'test\\_data', '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*',
        '.*']
    self.assertEqual(
        find_specs[artifact_types.TYPE_INDICATOR_FILE][9]._location_segments,
        path_segments)

    # Test expansion of user home directories
    find_specs = {}
    separator = '/'
    testuser1 = artifacts.UserAccountArtifact(
        user_directory='/homes/testuser1', username='testuser1')
    testuser2 = artifacts.UserAccountArtifact(
        user_directory='/home/testuser2', username='testuser2')
    user_accounts = [testuser1, testuser2]
    path_entry = '%%users.homedir%%/.thumbnails/**3'

    (artifact_filters.ArtifactDefinitionsFilterHelper.
    BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts,
        find_specs))

    # Six total find specs should be created for testuser1 and testuser2.
    self.assertEqual(len(find_specs[artifact_types.TYPE_INDICATOR_FILE]), 6)

    # Last entry in find_specs list should be testuser2 with a depth of 3
    path_segments = ['home', 'testuser2', '\\.thumbnails', '.*', '.*', '.*']
    self.assertEqual(
        find_specs[artifact_types.TYPE_INDICATOR_FILE][5]._location_segments,
        path_segments)


    # Test Windows path with profile directories and globs with a depth of 4.
    find_specs = {}
    separator = '\\'
    testuser1 = artifacts.UserAccountArtifact(
        user_directory='\\Users\\\\testuser1', username='testuser1')
    testuser2 = artifacts.UserAccountArtifact(
        user_directory='\\Users\\\\testuser2', username='testuser2')
    user_accounts = [testuser1, testuser2]
    path_entry = '%%users.homedir%%\\AppData\\**4'

    (artifact_filters.ArtifactDefinitionsFilterHelper.
    BuildFindSpecsFromFileArtifact(
        path_entry, separator, environment_variable, user_accounts,
        find_specs))

    # Eight find specs should be created for testuser1 and testuser2.
    self.assertEqual(len(find_specs[artifact_types.TYPE_INDICATOR_FILE]), 8)

    # Last entry in find_specs list should be testuser2, with a depth of 4.
    path_segments = ['Users', 'testuser2', 'AppData', '.*', '.*', '.*', '.*']
    self.assertEqual(
        find_specs[artifact_types.TYPE_INDICATOR_FILE][7]._location_segments,
        path_segments)


if __name__ == '__main__':
  unittest.main()
