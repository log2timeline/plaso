#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests the queue."""

import unittest

from plaso.lib import queue


class TestQueueConsumer(queue.QueueConsumer):
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

  def _ConsumeItem(self, item):
    """Consumes an item callback for ConsumeItems."""
    self.items.append(item)

  @property
  def number_of_items(self):
    """The items."""
    return len(self.items)


class MultiThreadedQueueTest(unittest.TestCase):
  """Tests the multi threaded queue."""

  _ITEMS = frozenset(['item1', 'item2', 'item3', 'item4'])

  def testPushPopItem(self):
    """Tests the PushItem and PopItem functions."""
    test_queue = queue.MultiThreadedQueue()

    for item in self._ITEMS:
      test_queue.PushItem(item)

    try:
      self.assertEquals(len(test_queue), len(self._ITEMS))
    except NotImplementedError:
      # On Mac OS X because of broken sem_getvalue()
      return

    test_queue.SignalEndOfInput()
    test_queue_consumer = TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, len(self._ITEMS))


class SingleThreadedQueueTest(unittest.TestCase):
  """Tests the single threaded queue."""

  _ITEMS = frozenset(['item1', 'item2', 'item3', 'item4'])

  def testPushPopItem(self):
    """Tests the PushItem and PopItem functions."""
    test_queue = queue.SingleThreadedQueue()

    for item in self._ITEMS:
      test_queue.PushItem(item)

    self.assertEquals(len(test_queue), len(self._ITEMS))

    test_queue.SignalEndOfInput()
    test_queue_consumer = TestQueueConsumer(test_queue)
    test_queue_consumer.ConsumeItems()

    self.assertEquals(test_queue_consumer.number_of_items, len(self._ITEMS))


if __name__ == '__main__':
  unittest.main()
