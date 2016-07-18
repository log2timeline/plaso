#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the engine."""

import os
import unittest

try:
  from guppy import hpy
except ImportError:
  hpy = None

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

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  def __init__(self):
    """Initialize the engine object."""
    super(TestEngine, self).__init__()

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'SOFTWARE'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SOFTWARE', test_file_path)
    test_file_path = self._GetTestFilePath([u'SYSTEM'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SYSTEM', test_file_path)

    self._file_system = file_system_builder.file_system
    self._mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

  def GetSourceFileSystem(self, source_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    Args:
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) of the file system.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None which will use the built in context
                        which is not multi process safe. Note that every thread
                        or process must have its own resolver context.

    Returns:
      A tuple of the file system (instance of dfvfs.FileSystem) and
      the mount point path specification (instance of path.PathSpec).
      The mount point path specification refers to either a directory or
      a volume on a storage media device or image. It is needed by the dfVFS
      file system searcher (instance of FileSystemSearcher) to indicate
      the base location of the file system.
    """
    self._file_system.Open(self._mount_point)
    return self._file_system, self._mount_point


class BaseEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the engine object."""

  # pylint: disable=protected-access

  def testGetSourceFileSystem(self):
    """Tests the GetSourceFileSystem function."""
    test_engine = engine.BaseEngine()

    source_path = os.path.join(self._TEST_DATA_PATH, u'ímynd.dd')
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

  def testPreprocessSources(self):
    """Tests the PreprocessSources function."""
    test_engine = TestEngine()

    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    test_engine.PreprocessSources([source_path_spec])

    self.assertEqual(test_engine.knowledge_base.platform, u'Windows')

    test_engine.PreprocessSources([None])

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    test_engine = engine.BaseEngine()

    self.assertFalse(test_engine._abort)
    test_engine.SignalAbort()
    self.assertTrue(test_engine._abort)

  def testSupportsMemoryProfiling(self):
    """Tests the SupportsMemoryProfiling function."""
    test_engine = engine.BaseEngine()

    expected_result = hpy is not None
    result = test_engine.SupportsMemoryProfiling()
    self.assertEqual(result, expected_result)


if __name__ == '__main__':
  unittest.main()
