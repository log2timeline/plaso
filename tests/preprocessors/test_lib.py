# -*- coding: utf-8 -*-
"""Preprocessing related functions and classes for testing."""

from dfvfs.helpers import fake_file_system_builder
from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfwinreg import registry as dfwinreg_registry

from plaso.containers import artifacts
from plaso.engine import knowledge_base
from plaso.preprocessors import manager

from tests import test_lib as shared_test_lib


class PreprocessPluginTestCase(shared_test_lib.BaseTestCase):
  """Preprocess plugin test case."""

  def _RunFileSystemPlugin(self, file_system, mount_point, plugin):
    """Runs a file system preprocess plugin.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      plugin (PreprocessPlugin): preprocess plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(searcher, knowledge_base_object)

    return knowledge_base_object

  def _RunWindowsRegistryPlugin(self, file_system, mount_point, plugin):
    """Runs a Windows Registry preprocess plugin.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      plugin (PreprocessPlugin): preprocess plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')

    registry_file_reader = manager.FileSystemWinRegistryFileReader(
        file_system, mount_point, environment_variables=[environment_variable])
    win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(win_registry, knowledge_base_object)

    return knowledge_base_object

  def _RunWindowsRegistryPluginOnSoftware(self, plugin):
    """Runs a Windows Registry preprocess plugin on a SOFTWARE file.

    Args:
      plugin (PreprocessPlugin): preprocess plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'SOFTWARE'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SOFTWARE', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    return self._RunWindowsRegistryPlugin(
        file_system_builder.file_system, mount_point, plugin)

  def _RunWindowsRegistryPluginOnSystem(self, plugin):
    """Runs a Windows Registry preprocess plugin on a SYSTEM file.

    Args:
      plugin (PreprocessPlugin): preprocess plugin.

    Return:
      KnowledgeBase: knowledge base filled with preprocessing information.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'SYSTEM'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SYSTEM', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    return self._RunWindowsRegistryPlugin(
        file_system_builder.file_system, mount_point, plugin)
