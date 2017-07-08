#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the engine."""

import unittest

try:
  from guppy import hpy
except ImportError:
  hpy = None

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.helpers import fake_file_system_builder
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import path_spec
from dfvfs.resolver import context
from dfvfs.vfs import file_system

from plaso.engine import engine

from tests import test_lib as shared_test_lib


class TestEngine(engine.BaseEngine):
  """Class that defines the processing engine for testing."""

  def __init__(self):
    """Initialize a test engine object."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = shared_test_lib.GetTestFilePath([u'SOFTWARE'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SOFTWARE', test_file_path)
    test_file_path = shared_test_lib.GetTestFilePath([u'SYSTEM'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SYSTEM', test_file_path)

    super(TestEngine, self).__init__()
    self._file_system = file_system_builder.file_system
    self._mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

  def GetSourceFileSystem(self, source_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    Args:
      source_path_spec (dfvfs.PathSpec): path specifications of the sources
          to process.
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
    self._file_system.Open(self._mount_point)
    return self._file_system, self._mount_point


class BaseEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the engine object."""

  # pylint: disable=protected-access

  # TODO: add tests for _GuessOS
  # TODO: add tests for CreateSession

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testGetSourceFileSystem(self):
    """Tests the GetSourceFileSystem function."""
    test_engine = engine.BaseEngine()

    source_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    resolver_context = context.Context()
    test_file_system, test_mount_point = test_engine.GetSourceFileSystem(
        source_path_spec, resolver_context=resolver_context)

    self.assertIsNotNone(test_file_system)
    self.assertIsInstance(test_file_system, file_system.FileSystem)

    self.assertIsNotNone(test_mount_point)
    self.assertIsInstance(test_mount_point, path_spec.PathSpec)

    test_file_system.Close()

    with self.assertRaises(RuntimeError):
      test_engine.GetSourceFileSystem(None)

  @shared_test_lib.skipUnlessHasTestFile([u'artifacts'])
  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testPreprocessSources(self):
    """Tests the PreprocessSources function."""
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()
    path = shared_test_lib.GetTestFilePath([u'artifacts'])
    registry.ReadFromDirectory(reader, path)

    test_engine = TestEngine()

    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    test_engine.PreprocessSources(registry, [source_path_spec])

    self.assertEqual(test_engine.knowledge_base.platform, u'Windows')

    test_engine.PreprocessSources(registry, [None])

  def testSupportsGuppyMemoryProfiling(self):
    """Tests the SupportsGuppyMemoryProfiling function."""
    test_engine = engine.BaseEngine()

    expected_result = hpy is not None
    result = test_engine.SupportsGuppyMemoryProfiling()
    self.assertEqual(result, expected_result)


if __name__ == '__main__':
  unittest.main()
