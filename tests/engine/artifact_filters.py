#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the artifacts file filter functions."""

import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher as dfwinreg_registry_searcher

from plaso.containers import artifacts
from plaso.engine import artifact_filters

from tests import test_lib as shared_test_lib


class ArtifactDefinitionsFiltersHelperTest(shared_test_lib.BaseTestCase):
  """Tests for artifact definitions filters helper."""

  # pylint: disable=protected-access

  def _CreateTestArtifactDefinitionsFiltersHelper(self):
    """Creates an artifact definitions filters helper for testing.

    Returns:
      ArtifactDefinitionsFiltersHelper: artifact definitions filters helper.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    registry.ReadFromDirectory(reader, test_artifacts_path)

    return artifact_filters.ArtifactDefinitionsFiltersHelper(registry)

  def _CreateTestUserAccounts(self):
    """Creates user accounts for testing Windows paths.

    Returns:
      list[UserAccountArtifact]: user accounts.
    """
    test_user1 = artifacts.UserAccountArtifact(
        identifier='1000', path_separator='\\',
        user_directory='C:\\Users\\testuser1',
        username='testuser1')

    test_user2 = artifacts.UserAccountArtifact(
        identifier='1001', path_separator='\\',
        user_directory='%SystemDrive%\\Users\\testuser2',
        username='testuser2')

    return [test_user1, test_user2]

  def testBuildFindSpecsWithFileSystem(self):
    """Tests the BuildFindSpecs function for file type artifacts."""
    test_file_path = self._GetTestFilePath(['System.evtx'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_1.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_3.txt'])
    self._SkipIfPathNotExists(test_file_path)

    artifact_filter_names = ['TestFiles', 'TestFiles2']
    test_filters_helper = self._CreateTestArtifactDefinitionsFiltersHelper()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemDrive', value='C:')
    test_user_accounts = self._CreateTestUserAccounts()

    test_filters_helper.BuildFindSpecs(
        artifact_filter_names, environment_variables=[environment_variable],
        user_accounts=test_user_accounts)

    self.assertEqual(len(test_filters_helper.file_system_find_specs), 16)
    self.assertEqual(len(test_filters_helper.registry_find_specs), 0)

    # Last find_spec should contain the testuser2 profile path.
    location_segments = sorted([
        find_spec._location_segments
        for find_spec in test_filters_helper.file_system_find_specs])
    path_segments = [
        'Users', 'testuser2', 'Documents', 'WindowsPowerShell', 'profile\\.ps1']
    self.assertEqual(location_segments[2], path_segments)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(
        find_specs=test_filters_helper.file_system_find_specs)
    self.assertIsNotNone(path_spec_generator)

    path_specs = list(path_spec_generator)

    # Two evtx, one symbolic link to evtx, one AUTHORS, two filter_*.txt files,
    # total 6 path specifications.
    self.assertEqual(len(path_specs), 6)

  def testBuildFindSpecsWithFileSystemAndGroup(self):
    """Tests the BuildFindSpecs function for file type artifacts."""
    test_file_path = self._GetTestFilePath(['System.evtx'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_1.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_3.txt'])
    self._SkipIfPathNotExists(test_file_path)

    artifact_filter_names = ['TestGroupExtract']
    test_filters_helper = self._CreateTestArtifactDefinitionsFiltersHelper()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemDrive', value='C:')
    test_user_accounts = self._CreateTestUserAccounts()

    test_filters_helper.BuildFindSpecs(
        artifact_filter_names, environment_variables=[environment_variable],
        user_accounts=test_user_accounts)

    self.assertEqual(len(test_filters_helper.file_system_find_specs), 16)
    self.assertEqual(len(test_filters_helper.registry_find_specs), 0)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(
        find_specs=test_filters_helper.file_system_find_specs)
    self.assertIsNotNone(path_spec_generator)

    path_specs = list(path_spec_generator)

    # Two evtx, one symbolic link to evtx, one AUTHORS, two filter_*.txt
    # files, which total 6 path specifications.
    self.assertEqual(len(path_specs), 6)

  def testBuildFindSpecsWithRegistry(self):
    """Tests the BuildFindSpecs function on Windows Registry sources."""
    artifact_filter_names = ['TestRegistry', 'TestRegistryValue']
    test_filters_helper = self._CreateTestArtifactDefinitionsFiltersHelper()

    test_filters_helper.BuildFindSpecs(artifact_filter_names)

    # There should be 3 Windows Registry find specifications.
    self.assertEqual(len(test_filters_helper.file_system_find_specs), 0)
    self.assertEqual(len(test_filters_helper.registry_find_specs), 3)

    file_entry = self._GetTestFileEntry(['SYSTEM'])
    file_object = file_entry.GetFileObject()

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage='cp1252', emulate_virtual_keys=False)
    registry_file.Open(file_object)

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    registry_file.SetKeyPathPrefix(key_path_prefix)
    win_registry.MapFile(key_path_prefix, registry_file)

    searcher = dfwinreg_registry_searcher.WinRegistrySearcher(win_registry)
    key_paths = list(searcher.Find(
        find_specs=test_filters_helper.registry_find_specs))

    self.assertIsNotNone(key_paths)
    self.assertEqual(len(key_paths), 8)

  def testCheckKeyCompatibility(self):
    """Tests the CheckKeyCompatibility function"""
    test_filter_file = self._CreateTestArtifactDefinitionsFiltersHelper()

    # Compatible Key.
    key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control'
    compatible_key = test_filter_file.CheckKeyCompatibility(key_path)
    self.assertTrue(compatible_key)

    # NOT a Compatible Key.
    key_path = 'HKEY_USERS\\S-1-5-18'
    compatible_key = test_filter_file.CheckKeyCompatibility(key_path)
    self.assertTrue(compatible_key)

  # TODO: add tests for _BuildFindSpecsFromArtifact
  # TODO: add tests for _BuildFindSpecsFromGroupName

  def testBuildFindSpecsFromFileSourcePath(self):
    """Tests the _BuildFindSpecsFromFileSourcePath function on file sources."""
    test_filter_file = self._CreateTestArtifactDefinitionsFiltersHelper()

    separator = '\\'
    test_user_accounts = []

    # Test expansion of environment variables.
    path_entry = '%%environ_systemroot%%\\test_data\\*.evtx'
    environment_variable = [artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')]

    find_specs = test_filter_file._BuildFindSpecsFromFileSourcePath(
        path_entry, separator, environment_variable, test_user_accounts)

    # Should build 1 find_spec.
    self.assertEqual(len(find_specs), 1)

    # Location segments should be equivalent to \Windows\test_data\*.evtx.
    # Underscores are not escaped in regular expressions in supported versions
    # of Python 3. See https://bugs.python.org/issue2650.
    expected_location_segments = ['Windows', 'test_data', '.*\\.evtx']

    self.assertEqual(
        find_specs[0]._location_segments, expected_location_segments)

    # Test expansion of globs.
    path_entry = '\\test_data\\**'
    find_specs = test_filter_file._BuildFindSpecsFromFileSourcePath(
        path_entry, separator, environment_variable, test_user_accounts)

    # Glob expansion should by default recurse ten levels.
    self.assertEqual(len(find_specs), 10)

    # Last entry in find_specs list should be 10 levels of depth.
    # Underscores are not escaped in regular expressions in supported versions
    # of Python 3. See https://bugs.python.org/issue2650
    expected_location_segments = ['test_data']

    expected_location_segments.extend([
        '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*', '.*'])

    self.assertEqual(
        find_specs[9]._location_segments, expected_location_segments)

    # Test expansion of user home directories
    separator = '/'
    test_user1 = artifacts.UserAccountArtifact(
        user_directory='/homes/testuser1', username='testuser1')
    test_user2 = artifacts.UserAccountArtifact(
        user_directory='/home/testuser2', username='testuser2')
    test_user_accounts = [test_user1, test_user2]

    path_entry = '%%users.homedir%%/.thumbnails/**3'
    find_specs = test_filter_file._BuildFindSpecsFromFileSourcePath(
        path_entry, separator, environment_variable, test_user_accounts)

    # 6 find specs should be created for testuser1 and testuser2.
    self.assertEqual(len(find_specs), 6)

    # Last entry in find_specs list should be testuser2 with a depth of 3
    expected_location_segments = [
        'home', 'testuser2', '\\.thumbnails', '.*', '.*', '.*']
    self.assertEqual(
        find_specs[5]._location_segments, expected_location_segments)

    # Test Windows path with profile directories and globs with a depth of 4.
    separator = '\\'
    test_user1 = artifacts.UserAccountArtifact(
        path_separator='\\', user_directory='C:\\Users\\testuser1',
        username='testuser1')
    test_user2 = artifacts.UserAccountArtifact(
        path_separator='\\', user_directory='%SystemDrive%\\Users\\testuser2',
        username='testuser2')
    test_user_accounts = [test_user1, test_user2]

    path_entry = '%%users.userprofile%%\\AppData\\**4'
    find_specs = test_filter_file._BuildFindSpecsFromFileSourcePath(
        path_entry, separator, environment_variable, test_user_accounts)

    # 8 find specs should be created for testuser1 and testuser2.
    self.assertEqual(len(find_specs), 8)

    # Last entry in find_specs list should be testuser2, with a depth of 4.
    expected_location_segments = [
        'Users', 'testuser2', 'AppData', '.*', '.*', '.*', '.*']
    self.assertEqual(
        find_specs[7]._location_segments, expected_location_segments)

    path_entry = '%%users.localappdata%%\\Microsoft\\**4'
    find_specs = test_filter_file._BuildFindSpecsFromFileSourcePath(
        path_entry, separator, environment_variable, test_user_accounts)

    # 16 find specs should be created for testuser1 and testuser2.
    self.assertEqual(len(find_specs), 16)

    # Last entry in find_specs list should be testuser2, with a depth of 4.
    expected_location_segments = [
        'Users', 'testuser2', 'Local\\ Settings', 'Application\\ Data',
        'Microsoft', '.*', '.*', '.*', '.*']
    self.assertEqual(
        find_specs[15]._location_segments, expected_location_segments)

  # TODO: add tests for _BuildFindSpecsFromRegistrySourceKey


if __name__ == '__main__':
  unittest.main()
