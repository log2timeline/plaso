#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the multi-process processing engine."""

import unittest

from plaso.engine import test_lib
from plaso.multi_processing import multi_process


class MultiProcessingQueueTest(unittest.TestCase):
  """Tests the multi-processing queue."""

  _ITEMS = frozenset(['item1', 'item2', 'item3', 'item4'])

  def testPushPopItem(self):
    """Tests the PushItem and PopItem functions."""
    test_queue = multi_process.MultiProcessingQueue()

    for item in self._ITEMS:
      test_queue.PushItem(item)

    try:
      self.assertEquals(len(test_queue), len(self._ITEMS))
    except NotImplementedError:
      # On Mac OS X because of broken sem_getvalue()
      return

    test_queue.SignalEndOfInput()
    test_queue_consumer = test_lib.TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, len(self._ITEMS))


if __name__ == '__main__':
  unittest.main()
