#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the multi-processing queue."""

import unittest

from plaso.engine import plaso_queue
from plaso.lib import errors
from plaso.multi_processing import multi_process_queue

from tests import test_lib as shared_test_lib


class TestQueueConsumer(object):
  """Class that implements the test queue consumer.

  The queue consumer subscribes to updates on the queue.

  Attributes:
    items (list[object]): queued items.
  """

  def __init__(self, queue):
    """Initializes the queue consumer.

    Args:
      queue (Queue): queue.
    """
    super(TestQueueConsumer, self).__init__()
    self._abort = False
    self._queue = queue
    self.items = []

  @property
  def number_of_items(self):
    """The number of items."""
    return len(self.items)

  def ConsumeItems(self):
    """Consumes the items that are pushed on the queue."""
    while not self._abort:
      try:
        item = self._queue.PopItem()

      except (errors.QueueClose, errors.QueueEmpty):
        break

      if isinstance(item, plaso_queue.QueueAbort):
        break

      self.items.append(item)


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

    test_queue_consumer = TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEqual(test_queue_consumer.number_of_items, len(self._ITEMS))


if __name__ == '__main__':
  unittest.main()
