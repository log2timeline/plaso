#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the multi-processing queue."""

import logging
import unittest

from plaso.multi_processing import multi_process_queue
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class QueueConsumer(object):
  """Class that implements the queue consumer interface.

  The consumer subscribes to updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the queue consumer.

    Args:
      queue_object: a queue object (instance of Queue).
    """
    super(QueueConsumer, self).__init__()
    self._abort = False
    self._queue = queue_object

  def SignalAbort(self):
    """Signals the consumer to abort."""
    self._abort = True


class ItemQueueConsumer(QueueConsumer):
  """Class that implements an item queue consumer.

  The consumer subscribes to updates on the queue.
  """

  def __init__(self, queue_object):
    """Initializes the item queue consumer.

    Args:
      queue_object: a queue object (instance of Queue).
    """
    super(ItemQueueConsumer, self).__init__(queue_object)
    self._number_of_consumed_items = 0

  @property
  def number_of_consumed_items(self):
    """The number of consumed items."""
    return self._number_of_consumed_items

  @abc.abstractmethod
  def _ConsumeItem(self, item, **kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      item: the item object.
      kwargs: keyword arguments to pass to the _ConsumeItem callback.
    """

  def ConsumeItems(self, **kwargs):
    """Consumes the items that are pushed on the queue.

    Args:
      kwargs: keyword arguments to pass to the _ConsumeItem callback.
    """
    while not self._abort:
      try:
        item = self._queue.PopItem()
      except (errors.QueueClose, errors.QueueEmpty) as exception:
        logging.debug(u'ConsumeItems exiting with exception {0:s}.'.format(
            type(exception)))
        break

      if isinstance(item, QueueAbort):
        logging.debug(u'ConsumeItems exiting, dequeued QueueAbort object.')
        break

      self._number_of_consumed_items += 1
      self._ConsumeItem(item, **kwargs)


class TestQueueConsumer(ItemQueueConsumer):
  """Class that implements the test queue consumer.

     The queue consumer subscribes to updates on the queue.
  """

  def __init__(self, test_queue):
    """Initializes the queue consumer.

    Args:
      test_queue: the test queue (instance of Queue).
    """
    super(TestQueueConsumer, self).__init__(test_queue)
    self.items = []

  def _ConsumeItem(self, item, **unused_kwargs):
    """Consumes an item callback for ConsumeItems."""
    self.items.append(item)

  @property
  def number_of_items(self):
    """The number of items."""
    return len(self.items)


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
