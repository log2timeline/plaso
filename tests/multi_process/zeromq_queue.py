#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the the zeromq queue."""

import unittest

from plaso.lib import errors
from plaso.multi_process import zeromq_queue

from tests import test_lib as shared_test_lib


class ZeroMQPullBindQueue(zeromq_queue.ZeroMQPullQueue):
  """A Plaso queue backed by a ZeroMQ PULL socket that binds to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = zeromq_queue.ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQPushConnectQueue(zeromq_queue.ZeroMQPushQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket that connects to a port.

  This queue may only be used to push items, not to pop.
  """
  SOCKET_CONNECTION_TYPE = zeromq_queue.ZeroMQQueue.SOCKET_CONNECTION_CONNECT


class ZeroMQRequestBindQueue(zeromq_queue.ZeroMQRequestQueue):
  """A Plaso queue backed by a ZeroMQ REQ socket that binds to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = zeromq_queue.ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQBufferedReplyConnectQueue(zeromq_queue.ZeroMQBufferedReplyQueue):
  """A Plaso queue backed by a ZeroMQ REP socket that connects to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = zeromq_queue.ZeroMQQueue.SOCKET_CONNECTION_CONNECT


class ZeroMQQueuesTest(shared_test_lib.BaseTestCase):
  """Tests for ZeroMQ queues."""

  # pylint: disable=protected-access

  _QUEUE_CLASSES = frozenset([
      zeromq_queue.ZeroMQPushBindQueue, ZeroMQPullBindQueue,
      ZeroMQRequestBindQueue])

  def _testItemTransferred(self, push_queue, pop_queue):
    """Tests than item can be transferred between two queues."""
    item = 'This is an item going from {0:s} to {1:s}.'.format(
        push_queue.name, pop_queue.name)
    push_queue.PushItem(item)
    popped_item = pop_queue.PopItem()
    self.assertEqual(item, popped_item)

  def testBufferedReplyQueue(self):
    """Tests for the buffered reply queue."""
    test_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        name='bufferedreply_bind', delay_open=False, linger_seconds=1)
    test_queue.PushItem('This is a test item.')
    test_queue.Close(abort=True)
    with self.assertRaises(errors.QueueAlreadyClosed):
      test_queue.PushItem('This shouldn\'t work')

  def testPushPullQueues(self):
    """Tests than an item can be transferred between push and pull queues."""
    push_queue = zeromq_queue.ZeroMQPushBindQueue(
        name='pushpull_pushbind', delay_open=False, linger_seconds=1)
    pull_queue = zeromq_queue.ZeroMQPullConnectQueue(
        name='pushpull_pullconnect', delay_open=False, port=push_queue.port,
        linger_seconds=1)
    self._testItemTransferred(push_queue, pull_queue)
    push_queue.Close()
    pull_queue.Close()
    pull_queue = ZeroMQPullBindQueue(
        name='pushpull_pullbind', delay_open=False, linger_seconds=1)
    push_queue = ZeroMQPushConnectQueue(
        name='pushpull_pushconnect', delay_open=False, port=pull_queue.port,
        linger_seconds=1)
    self._testItemTransferred(push_queue, pull_queue)
    push_queue.Close()
    pull_queue.Close()

  def testQueueStart(self):
    """Tests that delayed creation of ZeroMQ sockets occurs correctly."""
    for queue_class in self._QUEUE_CLASSES:
      queue_name = 'queuestart_{0:s}'.format(queue_class.__name__)
      test_queue = queue_class(
          name=queue_name, delay_open=True, linger_seconds=1)
      message = '{0:s} socket already exists.'.format(queue_name)
      self.assertIsNone(test_queue._zmq_socket, message)
      test_queue.Open()
      self.assertIsNotNone(test_queue._zmq_socket)
      test_queue.Close()

  def testRequestAndBufferedReplyQueues(self):
    """Tests REQ and buffered REP queue pairs."""
    reply_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        name='requestbufferedreply_replybind', delay_open=False,
        linger_seconds=1)
    request_queue = zeromq_queue.ZeroMQRequestConnectQueue(
        name='requestbufferedreply_requestconnect', delay_open=False,
        port=reply_queue.port, linger_seconds=1)
    self._testItemTransferred(reply_queue, request_queue)
    reply_queue.Close()
    request_queue.Close()
    request_queue = ZeroMQRequestBindQueue(
        name='requestbufferedreply_requestbind', delay_open=False,
        linger_seconds=1)
    reply_queue = ZeroMQBufferedReplyConnectQueue(
        name='requestbufferedreply_replyconnect', delay_open=False,
        port=request_queue.port, linger_seconds=0)
    self._testItemTransferred(reply_queue, request_queue)
    reply_queue.Close()
    request_queue.Close()

  def testEmptyBufferedQueues(self):
    """Tests the Empty method for buffered queues."""
    queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        name='requestbufferedreply_replybind', delay_open=False,
        linger_seconds=1, buffer_max_size=3, timeout_seconds=2,
        buffer_timeout_seconds=1)
    try:
      while True:
        queue.PushItem('item', block=False)
    except errors.QueueFull:
      # Queue is now full
      pass

    with self.assertRaises(errors.QueueFull):
      queue.PushItem('item', block=False)

    queue.Empty()
    # We should now be able to push another item without an exception.
    queue.PushItem('item')
    queue.Empty()
    queue.Close()

  def testSocketCreation(self):
    """Tests that ZeroMQ sockets are created when a new queue is created."""
    for queue_class in self._QUEUE_CLASSES:
      queue_name = 'socket_creation_{0:s}'.format(queue_class.__name__)
      test_queue = queue_class(
          name=queue_name, delay_open=False, linger_seconds=1)
      self.assertIsNotNone(test_queue._zmq_socket)
      test_queue.Close()


if __name__ == '__main__':
  unittest.main()
