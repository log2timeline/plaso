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

  @shared_test_lib.skipUnlessHasTestFile(['artifacts'])
  @shared_test_lib.skipUnlessHasTestFile(['System.evtx'])
  @shared_test_lib.skipUnlessHasTestFile(['testdir', 'filter_1.txt'])
  @shared_test_lib.skipUnlessHasTestFile(['testdir', 'filter_3.txt'])
  def testBuildFileFindSpecs(self):
    """Tests the BuildFindSpecs function for file type artifacts."""
    knowledge_base = knowledge_base_engine.KnowledgeBase()

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

    self.assertEqual(len(find_specs[artifact_types.TYPE_INDICATOR_FILE]), 13)

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
  def testBuildRegistryFindSpecs(self):
    """Tests the BuildFindSpecs function for registry artifacts."""
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

    # Three key paths found
    self.assertEqual(len(key_paths), 3)

if __name__ == '__main__':
  unittest.main()
