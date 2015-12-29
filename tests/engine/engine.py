#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the engine."""

import os
import unittest

try:
  from guppy import hpy
except ImportError:
  hpy = None

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import path_spec
from dfvfs.resolver import context
from dfvfs.vfs import file_system

from plaso.engine import engine

from tests import test_lib as shared_test_lib
from tests.engine import test_lib


class TestEngine(engine.BaseEngine):
  """Class that defines the processing engine for testing."""

  def __init__(self, path_spec_queue, event_object_queue, parse_error_queue):
    """Initialize the engine object.

    Args:
      path_spec_queue: the path specification queue object (instance of Queue).
      event_object_queue: the event object queue object (instance of Queue).
      parse_error_queue: the parser error queue object (instance of Queue).
    """
    super(TestEngine, self).__init__(
        path_spec_queue, event_object_queue, parse_error_queue)

    file_system_builder = shared_test_lib.FakeFileSystemBuilder()
    file_system_builder.AddTestFile(
        u'/Windows/System32/config/SOFTWARE', [u'SOFTWARE'])
    file_system_builder.AddTestFile(
        u'/Windows/System32/config/SYSTEM', [u'SYSTEM'])

    self._file_system = file_system_builder.file_system
    self._mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

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


class BaseEngineTest(test_lib.EngineTestCase):
  """Tests for the engine object."""

  def testGetSourceFileSystem(self):
    """Tests the GetSourceFileSystem function."""
    self._test_engine = engine.BaseEngine(None, None, None)

    source_path = os.path.join(self._TEST_DATA_PATH, u'ímynd.dd')
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    resolver_context = context.Context()
    test_file_system, test_mount_point = self._test_engine.GetSourceFileSystem(
        source_path_spec, resolver_context=resolver_context)

    self.assertIsNotNone(test_file_system)
    self.assertIsInstance(test_file_system, file_system.FileSystem)

    self.assertIsNotNone(test_mount_point)
    self.assertIsInstance(test_mount_point, path_spec.PathSpec)

    test_file_system.Close()

  def testPreprocessSources(self):
    """Tests the PreprocessSources function."""
    self._test_engine = TestEngine(None, None, None)

    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    self._test_engine.PreprocessSources([source_path_spec])

    self.assertEqual(self._test_engine.knowledge_base.platform, u'Windows')

  def testSetEnableDebugOutput(self):
    """Tests the SetDebugMode function."""
    self._test_engine = engine.BaseEngine(None, None, None)

    self._test_engine.SetEnableDebugOutput(True)

  def testSetEnableProfiling(self):
    """Tests the SetEnableProfiling function."""
    self._test_engine = engine.BaseEngine(None, None, None)

    self._test_engine.SetEnableProfiling(
        True, profiling_sample_rate=5000, profiling_type=u'all')

  def testSupportsMemoryProfiling(self):
    """Tests the SupportsMemoryProfiling function."""
    self._test_engine = engine.BaseEngine(None, None, None)

    expected_result = hpy is not None
    result = self._test_engine.SupportsMemoryProfiling()
    self.assertEqual(result, expected_result)


if __name__ == '__main__':
  unittest.main()
