#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the the zeromq queue."""

import unittest

from plaso.engine import zeromq_queue
from plaso.lib import errors

from tests import test_lib as shared_test_lib

import logging

logging.basicConfig(level=logging.DEBUG)


class testZeroMQQueues(shared_test_lib.BaseTestCase):
  """Tests for ZeroMQ queues."""

  # pylint: disable=protected-access

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
      queue_name = u'{0:s}_socket_creation'.format(queue_class.__name__)
      test_queue = queue_class(
          name=queue_name, delay_open=False, linger_seconds=1)
      self.assertIsNotNone(test_queue._zmq_socket)
      test_queue.Close()

  def testQueueStart(self):
    """Tests that delayed creation of ZeroMQ sockets occurs correctly."""
    for queue_class in self._QUEUE_CLASSES:
      queue_name = u'{0!s}_queue_start'.format(queue_class.__name__)
      test_queue = queue_class(
          name=queue_name, delay_open=True, linger_seconds=1)
      message = u'{0:s} socket already exists.'.format(queue_name)
      self.assertIsNone(test_queue._zmq_socket, message)
      test_queue.Open()
      self.assertIsNotNone(test_queue._zmq_socket)
      test_queue.Close()

  def testPushPullQueues(self):
    """Tests than an item can be transferred between push and pull queues."""
    push_queue = zeromq_queue.ZeroMQPushBindQueue(
        name=u'pushbind_pushpull', delay_open=False, linger_seconds=1)
    pull_queue = zeromq_queue.ZeroMQPullConnectQueue(
        name=u'pullconnect_pushpull', delay_open=False, port=push_queue.port,
        linger_seconds=1)
    self._testItemTransferred(push_queue, pull_queue)
    push_queue.Close()
    pull_queue.Close()
    pull_queue = zeromq_queue.ZeroMQPullBindQueue(
        name=u'pullbind_pushpull', delay_open=False, linger_seconds=1)
    push_queue = zeromq_queue.ZeroMQPushConnectQueue(
        name=u'pushconnect_pushpull', delay_open=False, port=pull_queue.port,
        linger_seconds=1)
    self._testItemTransferred(push_queue, pull_queue)
    push_queue.Close()
    pull_queue.Close()

  def testBufferedReplyQueue(self):
    """Tests for the buffered reply queue."""
    test_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        name=u'buffered_reply_bind', delay_open=False, linger_seconds=1)
    test_queue.PushItem(u'This is a test item.')
    test_queue.Empty()
    test_queue.Close()
    with self.assertRaises(errors.QueueAlreadyClosed):
      test_queue.PushItem(u'This shouldn\'t work')

  def testRequestAndBufferedReplyQueues(self):
    """Tests REQ and buffered REP queue pairs."""
    reply_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        name=u'bufferedreply_requestbuffer', delay_open=False, linger_seconds=1)
    request_queue = zeromq_queue.ZeroMQRequestConnectQueue(
        name=u'requestconnect_requestbuffer', delay_open=False,
        port=reply_queue.port, linger_seconds=1)
    self._testItemTransferred(reply_queue, request_queue)
    reply_queue.Close()
    request_queue.Close()
    request_queue = zeromq_queue.ZeroMQRequestBindQueue(
        name=u'requestbind_requestbuffer', delay_open=False, linger_seconds=1)
    reply_queue = zeromq_queue.ZeroMQBufferedReplyConnectQueue(
        name=u'replyconnect_requestbuffer', delay_open=False, port=request_queue.port, linger_seconds=0)
    self._testItemTransferred(reply_queue, request_queue)
    reply_queue.Close()
    request_queue.Close()


if __name__ == '__main__':
  unittest.main()
