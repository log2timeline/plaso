#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the the zeromq queue."""

import unittest

from plaso.engine import zeromq_queue
from plaso.lib import errors
from tests.engine import test_lib


class testZeroMQQueues(test_lib.EngineTestCase):
  """Tests for ZeroMQ queues."""

  _QUEUE_CLASSES = frozenset([
                              zeromq_queue.ZeroMQPushBindQueue,
                              zeromq_queue.ZeroMQPullBindQueue,
                              zeromq_queue.ZeroMQRequestBindQueue,
                              zeromq_queue.ZeroMQBufferedPullBindQueue,
                              zeromq_queue.ZeroMQBufferedPushBindQueue])

  def _testItemTransferred(self, push_queue, pop_queue):
    """Tests than item can be transferred between two queues."""
    item = u'This is an item.'
    push_queue.PushItem(item)
    popped_item = pop_queue.PopItem()
    self.assertEqual(item, popped_item)

  def testSocketCreation(self):
    """Tests that ZeroMQ sockets are created when a new queue is created."""
    for queue_class in self._QUEUE_CLASSES:
      test_queue = queue_class(delay_open=False)
      self.assertIsNotNone(test_queue._zmq_socket)

  def testQueueStart(self):
    """Tests that delayed creation of ZeroMQ sockets occurs correctly."""
    for queue_class in self._QUEUE_CLASSES:
      test_queue = queue_class(delay_open=True)
      self.assertIsNone(test_queue._zmq_socket)
      test_queue.Open()
      self.assertIsNotNone(test_queue._zmq_socket)

  def testPushPullQueues(self):
    """Tests than an item can be transferred between push and pull queues."""
    push_queue = zeromq_queue.ZeroMQPushBindQueue(delay_open=False)
    pull_queue = zeromq_queue.ZeroMQPullConnectQueue(
        delay_open=False, port=push_queue.port)
    self._testItemTransferred(push_queue, pull_queue)
    pull_queue = zeromq_queue.ZeroMQPullBindQueue(delay_open=False)
    push_queue = zeromq_queue.ZeroMQPushConnectQueue(
        delay_open=False, port=pull_queue.port)
    self._testItemTransferred(push_queue, pull_queue)

  def testBufferedReplyQueue(self):
    """Tests for the buffered reply queue."""
    test_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(delay_open=False)
    test_queue.PushItem(u'This is a test item.')
    test_queue.Empty()
    test_queue.Close()
    with self.assertRaises(errors.QueueAlreadyClosed):
      test_queue.PushItem(u'This shouldn\'t work')

  def testRequestAndBufferedReplyQueues(self):
    """Tests REQ and buffered REP queue pairs."""
    reply_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(delay_open=False)
    request_queue = zeromq_queue.ZeroMQRequestConnectQueue(
        delay_open=False, port=reply_queue.port)
    self._testItemTransferred(reply_queue, request_queue)
    request_queue = zeromq_queue.ZeroMQRequestBindQueue(delay_open=False)
    reply_queue = zeromq_queue.ZeroMQBufferedReplyConnectQueue(
        delay_open=False, port=request_queue.port)
    self._testItemTransferred(reply_queue, request_queue)


if __name__ == '__main__':
  unittest.main()
