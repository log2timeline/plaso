#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the single process processing engine."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.engine import single_process
from plaso.lib import errors

from tests.engine import test_lib


class SingleProcessEngineTest(test_lib.EngineTestCase):
  """Tests for the single process engine object."""

  def setUp(self):
    """Sets up the needed objects used throughout a test."""
    self._test_engine = single_process.SingleProcessEngine(
        maximum_number_of_queued_items=100)

  def testCreateCollector(self):
    """Tests the _CreateCollector function."""
    resolver_context = context.Context()

    test_collector = self._test_engine._CreateCollector(
        filter_find_specs=None, include_directory_stat=False,
        resolver_context=resolver_context)
    self.assertNotEqual(test_collector, None)
    self.assertIsInstance(
        test_collector, single_process.SingleProcessCollector)

  def testCreateExtractionWorker(self):
    """Tests the _CreateExtractionWorker function."""
    test_extraction_worker = self._test_engine._CreateExtractionWorker(0)
    self.assertNotEqual(test_extraction_worker, None)
    self.assertIsInstance(
        test_extraction_worker,
        single_process.SingleProcessEventExtractionWorker)

  def testProcessSources(self):
    """Tests the ProcessSources function."""
    source_path = os.path.join(self._TEST_DATA_PATH, u'ímynd.dd')
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    self._test_engine.PreprocessSources([source_path_spec])

    parser_filter_string = u'filestat'

    storage_writer = test_lib.TestStorageWriter(
        self._test_engine.event_object_queue)
    self._test_engine.ProcessSources(
        [source_path_spec], storage_writer,
        parser_filter_string=parser_filter_string)

    self.assertEqual(len(storage_writer.event_objects), 15)


class SingleProcessQueueTest(unittest.TestCase):
  """Tests the single process queue."""

  _ITEMS = frozenset([u'item1', u'item2', u'item3', u'item4'])

  def testPushPopItem(self):
    """Tests the PushItem and PopItem functions."""
    test_queue = single_process.SingleProcessQueue()

    for item in self._ITEMS:
      test_queue.PushItem(item)

    test_queue_consumer = test_lib.TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    expected_number_of_items = len(self._ITEMS)
    self.assertEqual(
        test_queue_consumer.number_of_items, expected_number_of_items)

  def testQueueEmpty(self):
    """Tests the queue raises the QueueEmpty exception."""
    test_queue = single_process.SingleProcessQueue()

    with self.assertRaises(errors.QueueEmpty):
      test_queue.PopItem()

  def testQueueFull(self):
    """Tests the queue raises the QueueFull exception."""
    test_queue = single_process.SingleProcessQueue(
        maximum_number_of_queued_items=5)

    for item in self._ITEMS:
      test_queue.PushItem(item)

    with self.assertRaises(errors.QueueFull):
      test_queue.PushItem(u'item5')

    with self.assertRaises(errors.QueueFull):
      test_queue.PushItem(u'item6')

    test_queue_consumer = test_lib.TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    expected_number_of_items = len(self._ITEMS)
    self.assertEqual(
        test_queue_consumer.number_of_items, expected_number_of_items + 1)


if __name__ == '__main__':
  unittest.main()
