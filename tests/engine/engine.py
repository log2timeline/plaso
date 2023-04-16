#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the engine."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import path_spec
from dfvfs.resolver import context
from dfvfs.vfs import file_system as dfvfs_file_system

from plaso.engine import configurations
from plaso.engine import engine
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class TestEngine(engine.BaseEngine):
  """Class that defines the processing engine for testing."""

  def __init__(self):
    """Initialize a test engine object."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = shared_test_lib.GetTestFilePath(['SOFTWARE'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SOFTWARE', test_file_path)
    test_file_path = shared_test_lib.GetTestFilePath(['SYSTEM'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SYSTEM', test_file_path)

    super(TestEngine, self).__init__()
    self._file_system = file_system_builder.file_system
    self._mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

  def GetSourceFileSystem(self, file_system_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    Args:
      file_system_path_spec (dfvfs.PathSpec): path specifications of
          the source file system to process.
      resolver_context (dfvfs.Context): resolver context.

    Returns:
      tuple: containing:

        dfvfs.FileSystem: file system
        path.PathSpec: mount point path specification. The mount point path
            specification refers to either a directory or a volume on a storage
            media device or image. It is needed by the dfVFS file system
            searcher (FileSystemSearcher) to indicate the base location of
            the file system
    """
    return self._file_system, self._mount_point


class BaseEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the engine object."""

  # pylint: disable=protected-access

  def testStartStopProfiling(self):
    """Tests the _StartProfiling and _StopProfiling functions."""
    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.profiling.directory = temp_directory
      configuration.profiling.profilers = set([
          'memory', 'parsers', 'processing', 'serializers', 'storage',
          'task_queue'])

      test_engine = engine.BaseEngine()

      test_engine._StartProfiling(None)

      test_engine._StartProfiling(configuration.profiling)
      test_engine._StopProfiling()

  def testBuildArtifactsRegistry(self):
    """Tests the BuildArtifactsRegistry function."""
    test_artifacts_path = shared_test_lib.GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_engine = TestEngine()

    self.assertIsNone(test_engine._artifacts_registry)

    test_engine.BuildArtifactsRegistry(test_artifacts_path, None)

    self.assertIsNotNone(test_engine._artifacts_registry)

    # TODO: add test that raises BadConfigOption

  # TODO: add tests for BuildCollectionFilters.

  def testCreateSession(self):
    """Tests the CreateSession function."""
    test_engine = engine.BaseEngine()

    session = test_engine.CreateSession()
    self.assertIsNotNone(session)

  def testGetSourceFileSystem(self):
    """Tests the GetSourceFileSystem function."""
    test_engine = engine.BaseEngine()

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=os_path_spec)

    resolver_context = context.Context()
    test_file_system, test_mount_point = test_engine.GetSourceFileSystem(
        source_path_spec, resolver_context=resolver_context)

    self.assertIsNotNone(test_file_system)
    self.assertIsInstance(test_file_system, dfvfs_file_system.FileSystem)

    self.assertIsNotNone(test_mount_point)
    self.assertIsInstance(test_mount_point, path_spec.PathSpec)

    with self.assertRaises(RuntimeError):
      test_engine.GetSourceFileSystem(None)

  def testPreprocessSource(self):
    """Tests the PreprocessSource function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    test_artifacts_path = shared_test_lib.GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_engine = TestEngine()
    test_engine.BuildArtifactsRegistry(test_artifacts_path, None)

    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    source_configurations = test_engine.PreprocessSource(
        [source_path_spec], storage_writer)

    self.assertEqual(len(source_configurations), 1)
    self.assertEqual(source_configurations[0].operating_system, 'Windows NT')


if __name__ == '__main__':
  unittest.main()
