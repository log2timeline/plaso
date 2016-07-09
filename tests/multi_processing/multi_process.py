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
from plaso.multi_processing import engine
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.engine import test_lib as engine_test_lib


class MultiProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the multi-process engine object."""

  def testProcessSources(self):
    """Tests the PreprocessSources and ProcessSources function."""
    test_engine = engine.MultiProcessEngine(
        maximum_number_of_queued_items=100)

    source_path = os.path.join(self._TEST_DATA_PATH, u'ímynd.dd')
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_engine.PreprocessSources([source_path_spec])

    session = sessions.Session()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, temp_file)

      preprocess_object = event.PreprocessObject()
      test_engine.ProcessSources(
          session.identifier, [source_path_spec], preprocess_object,
          storage_writer, parser_filter_expression=u'filestat')

    # TODO: implement a way to obtain the results without relying
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
