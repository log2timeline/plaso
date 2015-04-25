#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the single process processing engine."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.helpers import file_system_searcher
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.engine import single_process
from plaso.engine import test_lib
from plaso.lib import errors


class SingleProcessQueueTest(unittest.TestCase):
  """Tests the single process queue."""

  _ITEMS = frozenset(['item1', 'item2', 'item3', 'item4'])

  def testPushPopItem(self):
    """Tests the PushItem and PopItem functions."""
    test_queue = single_process.SingleProcessQueue()

    for item in self._ITEMS:
      test_queue.PushItem(item)

    test_queue.SignalEndOfInput()
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
      test_queue.PushItem('item5')

    with self.assertRaises(errors.QueueFull):
      test_queue.PushItem('item6')

    test_queue_consumer = test_lib.TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    expected_number_of_items = len(self._ITEMS)
    self.assertEqual(
        test_queue_consumer.number_of_items, expected_number_of_items + 1)


class SingleProcessEngineTest(unittest.TestCase):
  """Tests for the engine object."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  def testEngine(self):
    """Test the engine functionality."""
    resolver_context = context.Context()
    test_engine = single_process.SingleProcessEngine(
        maximum_number_of_queued_items=25000)

    self.assertNotEqual(test_engine, None)

    source_path = os.path.join(self._TEST_DATA_PATH, u'ímynd.dd')
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_engine.SetSource(source_path_spec, resolver_context=resolver_context)

    self.assertFalse(test_engine.SourceIsDirectory())
    self.assertFalse(test_engine.SourceIsFile())
    self.assertTrue(test_engine.SourceIsStorageMediaImage())

    test_file_system, test_searcher = test_engine.GetSourceFileSystemSearcher(
        resolver_context=resolver_context)
    self.assertNotEqual(test_searcher, None)
    self.assertIsInstance(
        test_searcher, file_system_searcher.FileSystemSearcher)

    test_file_system.Close()

    test_engine.PreprocessSource('Windows')

    test_collector = test_engine.CreateCollector(
        False, vss_stores=None, filter_find_specs=None,
        resolver_context=resolver_context)
    self.assertNotEqual(test_collector, None)
    self.assertIsInstance(
        test_collector, single_process.SingleProcessCollector)

    test_extraction_worker = test_engine.CreateExtractionWorker(0)
    self.assertNotEqual(test_extraction_worker, None)
    self.assertIsInstance(
        test_extraction_worker,
        single_process.SingleProcessEventExtractionWorker)


if __name__ == '__main__':
  unittest.main()
