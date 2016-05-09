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
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.storage import zip_file as storage_zip_file

from tests.engine import test_lib


class TestPathSpecQueueConsumer(plaso_queue.ItemQueueConsumer):
  """Class that implements a test path specification queue consumer."""

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(TestPathSpecQueueConsumer, self).__init__(queue_object)
    self.path_specs = []

  def _ConsumeItem(self, path_spec_object, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      path_spec_object: a path specification (instance of dfvfs.PathSpec).
    """
    self.path_specs.append(path_spec_object)

  @property
  def number_of_path_specs(self):
    """The number of path specifications."""
    return len(self.path_specs)

  def GetFilePaths(self):
    """Retrieves a list of file paths from the path specifications."""
    file_paths = []
    for path_spec_object in self.path_specs:
      data_stream = getattr(path_spec_object, u'data_stream', None)
      location = getattr(path_spec_object, u'location', None)
      if location is not None:
        if data_stream:
          location = u'{0:s}:{1:s}'.format(location, data_stream)
        file_paths.append(location)

    return file_paths


class TestEngine(engine.BaseEngine):
  """Class that defines the processing engine for testing."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  def __init__(self, path_spec_queue, event_object_queue, parse_error_queue):
    """Initialize the engine object.

    Args:
      path_spec_queue: the path specification queue object (instance of Queue).
      event_object_queue: the event object queue object (instance of Queue).
      parse_error_queue: the parser error queue object (instance of Queue).
    """
    super(TestEngine, self).__init__(
        path_spec_queue, event_object_queue, parse_error_queue)

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


class BaseEngineTest(test_lib.EngineTestCase):
  """Tests for the engine object."""

  def testGetSourceFileSystem(self):
    """Tests the GetSourceFileSystem function."""
    test_engine = engine.BaseEngine(None, None, None)

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

  def testPreprocessSources(self):
    """Tests the PreprocessSources function."""
    test_engine = TestEngine(None, None, None)

    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    test_engine.PreprocessSources([source_path_spec])

    self.assertEqual(test_engine.knowledge_base.platform, u'Windows')

  def testSetEnableDebugOutput(self):
    """Tests the SetDebugMode function."""
    test_engine = engine.BaseEngine(None, None, None)

    test_engine.SetEnableDebugOutput(True)

  def testSetEnableProfiling(self):
    """Tests the SetEnableProfiling function."""
    test_engine = engine.BaseEngine(None, None, None)

    test_engine.SetEnableProfiling(
        True, profiling_sample_rate=5000, profiling_type=u'all')

  def testSupportsMemoryProfiling(self):
    """Tests the SupportsMemoryProfiling function."""
    test_engine = engine.BaseEngine(None, None, None)

    expected_result = hpy is not None
    result = test_engine.SupportsMemoryProfiling()
    self.assertEqual(result, expected_result)


class PathSpecQueueProducerTest(test_lib.EngineTestCase):
  """Tests for the path specification producer object."""

  def testRun(self):
    """Tests the Run function."""
    test_file = self._GetTestFilePath([u'storage.json.plaso'])
    storage_object = storage_zip_file.StorageFile(
        test_file, read_only=True)

    test_path_spec_queue = single_process.SingleProcessQueue()
    test_collector = engine.PathSpecQueueProducer(
        test_path_spec_queue, storage_object)
    test_collector.Run()

    test_collector_queue_consumer = TestPathSpecQueueConsumer(
        test_path_spec_queue)
    test_collector_queue_consumer.ConsumeItems()

    self.assertEqual(test_collector_queue_consumer.number_of_path_specs, 2)

    expected_path_specs = [
        u'type: OS, location: /tmp/test/test_data/syslog\n',
        u'type: OS, location: /tmp/test/test_data/syslog\n']

    path_specs = []
    for path_spec_object in test_collector_queue_consumer.path_specs:
      path_specs.append(path_spec_object.comparable)

    self.assertEqual(sorted(path_specs), sorted(expected_path_specs))


if __name__ == '__main__':
  unittest.main()
