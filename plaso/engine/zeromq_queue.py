# -*- coding: utf-8 -*-
"""ZeroMQ implementations of the Plaso queue interface."""

import logging
import zmq

from plaso.engine import queue
from plaso.lib import errors

class QueueAlreadyStarted(errors.Error):
  """Raised when an attempt is made to start queue that's already started."""


class QueueAlreadyClosed(errors.Error):
  """Raised when an attempt is made to close a queue that's already closed."""


class ZeroMQQueue(queue.Queue):
  """Class that defines an interfaces for ZeroMQ backed Plaso queues.

  Attributes:
    port: The TCP port that the queue is connected or bound to. If the queue is
          not yet bound or connected to a port, this value will be None.
  """
  def __init__(
      self, socket_type, connect=False, delay_start=True, linger_seconds=10,
      port=None, timeout_seconds=5):
    """Creates a ZeroMQ backed queue.

    Args:
      socket_type: The ZeroMQ socket type to use to create the underlying
                   ZeroMQ socket. This argument must be one of the ZeroMQ
                   socket types defined in zmq.
      connect: Whether this queue should connect or bind to the given port. The
               default is False, which indicates that the queue should bind. If
               this argument is True, a value for the 'port' argument must be
               specified.
      delay_start: whether a ZeroMQ socket should be created the first time the
                   queue is pushed to or popped from, rather than at queue
                   object initialization. This is useful if a queue needs to be
                   passed to a child process from a parent. The default is True.
      linger_seconds: The number of seconds that the underlying ZeroMQ socket
                      can remain open after the queue object has been closed, to
                      enable queued items to be transferred to other ZeroMQ
                      sockets.
      port: The TCP port to use for the queue. The default is None, which
            indicates that the queue should choose a random port to bind to.
      timeout_seconds: The number of seconds that calls to PopItem and PushItem
                       may block for, before returning queue.QueueEmpty.
    """
    if connect and not port:
      raise AttributeError(u'No port specified to connect to.')
    self.port = port
    self._connect = connect
    self._linger_seconds = linger_seconds
    self._zmq_socket = None
    self._timeout_milliseconds = timeout_seconds * 1000
    self._socket_type = socket_type
    if not delay_start:
      self._CreateZMQSocket()


  def _CreateZMQSocket(self):
    """Creates a ZeroMQ socket to back this queue interface."""
    zmq_context = zmq.Context()
    self._zmq_socket = zmq_context.socket(self._socket_type)

    if self._socket_type == zmq.PULL or self._socket_type == zmq.SUB:
      self._zmq_socket.setsockopt(
          zmq.RCVTIMEO, self._timeout_milliseconds)
    elif self._socket_type == zmq.PUSH or self._socket_type == zmq.PUB:
      self._zmq_socket.setsockopt(
          zmq.SNDTIMEO, self._timeout_milliseconds)

    if self._connect:
      address = u'tcp://127.0.0.1:{0}'.format(self.port)
      logging.debug(u'Connecting to {0:s}'.format(address))
      self._zmq_socket.connect(address)
    elif self.port:
      address = u'tcp://127.0.0.1:{0}'.format(self.port)
      logging.debug(u'Binding to {0:s}'.format(address))
      self._zmq_socket.bind(address)
    else:
      self.port = self._zmq_socket.bind_to_random_port(u'tcp://127.0.0.1')
      logging.info(u'Bound to random port {0:d}'.format(self.port))

  def Start(self):
    """Starts this queue, causing the creation of a ZeroMQ socket.

    Raises:
      QueueAlreadyStarted: If the queue is already started, and a socket already
      exists.
    """
    if self._zmq_socket:
      raise QueueAlreadyStarted
    self._CreateZMQSocket()

  def Close(self):
    """Closes the queue.

    Raises:
      QueueAlreadyClosed: If the queue is not started, or has already been
      closed.
    """
    if not self._zmq_socket:
      raise QueueAlreadyClosed
    self._zmq_socket.close(self._linger_seconds)

  def IsEmpty(self):
    """Checks if the queue is empty.

    ZeroMQ queues don't have a concept of "empty" - there could always be
    messages on the queue that a producer or consumer is unaware of. Thus,
    the queue is never empty, so we return False.

    Returns:
      False
    """
    return False

  def PushItem(self, item):
    """Pushes an item on to the queue."""
    raise NotImplementedError

  def PopItem(self):
    """Pops an item off the queue."""
    raise NotImplementedError


class ZeroMQPullQueue(ZeroMQQueue):
  """A Plaso queue backed by a ZeroMQ PULL socket.

  This queue may only be used to pop items, not to push.
  """
  def __init__(
      self, connect=False, delay_start=True, linger_seconds=10,
      port=None, timeout_seconds=5):
    """Initializes a ZeroMQPullQueue.

    Args:
      connect: Whether this queue should connect or bind to the given port. The
               default is False, which indicates that the queue should bind.
      delay_start: whether a ZeroMQ socket should be created the first time the
                   queue is pushed to or popped from, rather than at queue
                   object initialization. This is useful if a queue needs to be
                   passed to a child process from a parent. The default is True.
      linger_seconds: The number of seconds that the underlying ZeroMQ socket
                      can remain open after the queue object has been closed, to
                      enable queued items to be transferred to other ZeroMQ
                      sockets.
      port: The TCP port to use for the queue. The default is None, which
            indicates that the queue should choose a random port to bind to.
      timeout_seconds: The number of seconds that calls to PopItem and PushItem
                       may block for, before returning queue.QueueEmpty."""
    super(ZeroMQPullQueue, self).__init__(
        zmq.PULL, connect=connect, delay_start=delay_start,
        linger_seconds=linger_seconds, port=port,
        timeout_seconds=timeout_seconds)

  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      errors.QueueEmpty: If the queue is empty, and no item could be popped.
    """
    if not self._zmq_socket:
      self._CreateZMQSocket()
    try:
      item = self._zmq_socket.recv_pyobj()
      return item
    except zmq.error.Again:
      raise errors.QueueEmpty

  def PushItem(self, item):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.
    """
    raise NotImplementedError


class ZeroMQPushQueue(ZeroMQQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket.

  This queue may only be used to push items, not to pop.
  """
  def __init__(
      self, connect=False, delay_start=True, linger_seconds=10,
      port=None, timeout_seconds=5):
    """Initializes a ZeroMQ producer queue.

    Args:
      connect: Whether this queue should connect or bind to the given port. The
               default is False, which indicates that the queue should bind.
      delay_start: whether a ZeroMQ socket should be created the first time the
                   queue is pushed to or popped from, rather than at queue
                   object initialization. This is useful if a queue needs to be
                   passed to a child process from a parent. The default is True.
      linger_seconds: The number of seconds that the underlying ZeroMQ socket
                      can remain open after the queue object has been closed, to
                      enable queued items to be transferred to other ZeroMQ
                      sockets.
      port: The TCP port to use for the queue. The default is None, which
            indicates that the queue should choose a random port to bind to.
      timeout_seconds: The number of seconds that calls to PopItem and PushItem
                       may block for, before returning queue.QueueEmpty."""
    super(ZeroMQPushQueue, self).__init__(
        zmq.PUSH, connect=connect, delay_start=delay_start,
        linger_seconds=linger_seconds, port=port,
        timeout_seconds=timeout_seconds)

  def PopItem(self):
    """Pops an item of the queue.

    Provided for compatibility with the API, but doesn't actually work.
    """
    raise NotImplementedError

  def PushItem(self, item):
    """Push an item on to the queue."""
    if not self._zmq_socket:
      self._CreateZMQSocket()
    self._zmq_socket.send_pyobj(item)
