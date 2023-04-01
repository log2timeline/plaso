# -*- coding: utf-8 -*-
"""Preprocessing related functions and classes for testing."""

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.helpers import fake_file_system_builder
from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher

from plaso.containers import artifacts
from plaso.preprocessors import manager
from plaso.preprocessors import mediator
from plaso.storage.fake import writer as fake_writer

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

  def _CreateTestStorageWriter(self):
    """Creates a storage writer for testing purposes.

    Returns:
      StorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    return storage_writer

  def _RunPreprocessorPluginOnFileSystem(
      self, file_system, mount_point, storage_writer, plugin):
    """Runs a preprocessor plugin on a file system.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      storage_writer (StorageWriter): storage writer.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      PreprocessMediator: preprocess mediator.
    """
    artifact_definition = self._artifacts_registry.GetDefinitionByName(
        plugin.ARTIFACT_DEFINITION_NAME)
    self.assertIsNotNone(artifact_definition)

    test_mediator = mediator.PreprocessMediator(storage_writer)

    searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)

    plugin.Collect(test_mediator, artifact_definition, searcher, file_system)

    return test_mediator

  def _RunPreprocessorPluginOnWindowsRegistryValue(
      self, file_system, mount_point, storage_writer, plugin):
    """Runs a preprocessor plugin on a Windows Registry value.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      storage_writer (StorageWriter): storage writer.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      PreprocessMediator: preprocess mediator.
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

    test_mediator = mediator.PreprocessMediator(storage_writer)

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    plugin.Collect(test_mediator, artifact_definition, searcher)

    return test_mediator

  def _RunPreprocessorPluginOnWindowsRegistryValueSoftware(
      self, storage_writer, plugin):
    """Runs a preprocessor plugin on a Windows Registry value in SOFTWARE.

    Args:
      storage_writer (StorageWriter): storage writer.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      PreprocessMediator: preprocess mediator.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SOFTWARE', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    return self._RunPreprocessorPluginOnWindowsRegistryValue(
        file_system_builder.file_system, mount_point, storage_writer, plugin)

  def _RunPreprocessorPluginOnWindowsRegistryValueSystem(
      self, storage_writer, plugin):
    """Runs a preprocessor plugin on a Windows Registry value in SYSTEM.

    Args:
      storage_writer (StorageWriter): storage writer.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      PreprocessMediator: preprocess mediator.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SYSTEM', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    return self._RunPreprocessorPluginOnWindowsRegistryValue(
        file_system_builder.file_system, mount_point, storage_writer, plugin)
