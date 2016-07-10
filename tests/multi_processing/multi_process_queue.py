#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the multi-processing queue."""

import unittest

from plaso.multi_processing import multi_process_queue
from tests import test_lib as shared_test_lib
from tests.engine import test_lib as engine_test_lib


class MultiProcessingQueueTest(shared_test_lib.BaseTestCase):
  """Tests the multi-processing queue object."""

  _ITEMS = frozenset([u'item1', u'item2', u'item3', u'item4'])

  def testPushPopItem(self):
    """Tests the PushItem and PopItem functions."""
    # A timeout is used to prevent the multi processing queue to close and
    # stop blocking the current process
    test_queue = multi_process_queue.MultiProcessingQueue(timeout=0.1)

    for item in self._ITEMS:
      test_queue.PushItem(item)

    test_queue_consumer = engine_test_lib.TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEqual(test_queue_consumer.number_of_items, len(self._ITEMS))


if __name__ == '__main__':
  unittest.main()
