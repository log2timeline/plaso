#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the multi-process processing engine."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import sessions
from plaso.lib import event
from plaso.multi_processing import multi_process
from plaso.engine import plaso_queue
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.engine import test_lib as engine_test_lib


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


class MultiProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the multi-process engine object."""

  def testProcessSources(self):
    """Tests the PreprocessSources and ProcessSources function."""
    test_engine = multi_process.MultiProcessEngine(
        maximum_number_of_queued_items=100)

    source_path = os.path.join(self._TEST_DATA_PATH, u'ímynd.dd')
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_engine.PreprocessSources([source_path_spec])

    session_start = sessions.SessionStart()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = storage_zip_file.ZIPStorageFileWriter(temp_file)

      preprocess_object = event.PreprocessObject()
      test_engine.ProcessSources(
          [source_path_spec], session_start, preprocess_object, storage_writer,
          parser_filter_expression=u'filestat')

    # TODO: implement a way to obtain the resuls without relying
    # on multi-process primitives e.g. by writing to a file.
    # self.assertEqual(len(storage_writer.events), 15)


class MultiProcessingQueueTest(shared_test_lib.BaseTestCase):
  """Tests the multi-processing queue object."""

  _ITEMS = frozenset([u'item1', u'item2', u'item3', u'item4'])

  def testPushPopItem(self):
    """Tests the PushItem and PopItem functions."""
    # A timeout is used to prevent the multi processing queue to close and
    # stop blocking the current process
    test_queue = multi_process.MultiProcessingQueue(timeout=0.1)

    for item in self._ITEMS:
      test_queue.PushItem(item)

    test_queue_consumer = engine_test_lib.TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEqual(test_queue_consumer.number_of_items, len(self._ITEMS))


if __name__ == '__main__':
  unittest.main()
