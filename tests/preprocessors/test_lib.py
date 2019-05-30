# -*- coding: utf-8 -*-
"""Preprocessing related functions and classes for testing."""

from __future__ import unicode_literals

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.helpers import fake_file_system_builder
from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher

from plaso.containers import artifacts
from plaso.engine import knowledge_base
from plaso.preprocessors import manager

from tests import test_lib as shared_test_lib


class ArtifactPreprocessorPluginTestCase(shared_test_lib.BaseTestCase):
  """Artifact preprocessor plugin test case."""

  @classmethod
  def setUpClass(cls):
    """Makes preparations before running any of the tests."""
    artifacts_path = shared_test_lib.GetTestFilePath(['artifacts'])
    cls._artifacts_registry = artifacts_registry.ArtifactDefinitionsRegistry()

    reader = artifacts_reader.YamlArtifactsReader()
    cls._artifacts_registry.ReadFromDirectory(reader, artifacts_path)

  def _RunPreprocessorPluginOnFileSystem(
      self, file_system, mount_point, plugin):
    """Runs a preprocessor plugin on a file system.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    artifact_definition = self._artifacts_registry.GetDefinitionByName(
        plugin.ARTIFACT_DEFINITION_NAME)
    self.assertIsNotNone(artifact_definition)

    knowledge_base_object = knowledge_base.KnowledgeBase()

    searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)

    plugin.Collect(
        knowledge_base_object, artifact_definition, searcher, file_system)

    return knowledge_base_object

  def _RunPreprocessorPluginOnWindowsRegistryValue(
      self, file_system, mount_point, plugin):
    """Runs a preprocessor plugin on a Windows Registry value.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    artifact_definition = self._artifacts_registry.GetDefinitionByName(
        plugin.ARTIFACT_DEFINITION_NAME)
    self.assertIsNotNone(artifact_definition)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    registry_file_reader = manager.FileSystemWinRegistryFileReader(
        file_system, mount_point, environment_variables=[environment_variable])
    win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)

    knowledge_base_object = knowledge_base.KnowledgeBase()

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    plugin.Collect(knowledge_base_object, artifact_definition, searcher)

    return knowledge_base_object

  def _RunPreprocessorPluginOnWindowsRegistryValueSoftware(self, plugin):
    """Runs a preprocessor plugin on a Windows Registry value in SOFTWARE.

    Args:
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SOFTWARE', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    return self._RunPreprocessorPluginOnWindowsRegistryValue(
        file_system_builder.file_system, mount_point, plugin)

  def _RunPreprocessorPluginOnWindowsRegistryValueSystem(self, plugin):
    """Runs a preprocessor plugin on a Windows Registry value in SYSTEM.

    Args:
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SYSTEM', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    return self._RunPreprocessorPluginOnWindowsRegistryValue(
        file_system_builder.file_system, mount_point, plugin)
