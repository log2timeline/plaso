#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the the zeromq queue."""

import unittest

from plaso.engine import zeromq_queue
from tests.engine import test_lib


class testZeroMQPushPullQueues(test_lib.EngineTestCase):
  """Tests for the Push and Pull type ZeroMQ queues."""

  def testSocketCreation(self):
    """Tests that ZeroMQ sockets are created when a new queue is created."""
    push_queue = zeromq_queue.ZeroMQPushBindQueue(delay_start=False)
    pull_queue = zeromq_queue.ZeroMQPullBindQueue(delay_start=False)
    self.assertIsNotNone(push_queue._zmq_socket)
    self.assertIsNotNone(pull_queue._zmq_socket)

  def testQueueStart(self):
    """Tests that delayed creation of ZeroMQ sockets occurs correctly."""
    push_queue = zeromq_queue.ZeroMQPushBindQueue(delay_start=True)
    pull_queue = zeromq_queue.ZeroMQPullBindQueue(delay_start=True)
    self.assertIsNone(push_queue._zmq_socket)
    self.assertIsNone(pull_queue._zmq_socket)
    push_queue.Start()
    self.assertIsNotNone(push_queue._zmq_socket)
    pull_queue.Start()
    self.assertIsNotNone(pull_queue._zmq_socket)

  def testItemCanBeQueuedAndDequeued(self):
    """Tests than an item can be transferred between push and pull queues."""
    push_queue = zeromq_queue.ZeroMQPushBindQueue(delay_start=False)
    pull_queue = zeromq_queue.ZeroMQPullConnectQueue(
        delay_start=False, port=push_queue.port)
    item = u'This is an item.'
    push_queue.PushItem(item)
    popped_item = pull_queue.PopItem()
    self.assertEqual(item, popped_item)


if __name__ == '__main__':
  unittest.main()
