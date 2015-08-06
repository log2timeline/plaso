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
    self.name = u'Unnamed'
    if not delay_start:
      self._CreateZMQSocket()

  @property
  def timeout_seconds(self):
    return self._timeout_milliseconds / 1000

  @timeout_seconds.setter
  def timeout_seconds(self, value):
    """The number of seconds that a PopItem or PushItem call can block for."""
    self._timeout_milliseconds = value * 1000
    self._SetSocketTimeouts()

  def _SetSocketTimeouts(self):
    """Set the timeouts for the socket send/receive."""
    if self._socket_type == zmq.PULL:
      self._zmq_socket.setsockopt(
          zmq.RCVTIMEO, self._timeout_milliseconds)
    elif self._socket_type == zmq.PUSH:
      self._zmq_socket.setsockopt(
          zmq.SNDTIMEO, self._timeout_milliseconds)

  def _CreateZMQSocket(self):
    """Creates a ZeroMQ socket to back this queue interface."""
    zmq_context = zmq.Context()
    self._zmq_socket = zmq_context.socket(self._socket_type)
    self._SetSocketTimeouts()

    if self._connect:
      address = u'tcp://127.0.0.1:{0}'.format(self.port)
      logging.debug(u'{0:s} Connecting to {1:s}'.format(self.name, address))
      self._zmq_socket.connect(address)
    elif self.port:
      address = u'tcp://127.0.0.1:{0}'.format(self.port)
      logging.debug(u'{0:s} Binding to {1:s}'.format(self.name, address))
      self._zmq_socket.bind(address)
    else:
      self.port = self._zmq_socket.bind_to_random_port(u'tcp://127.0.0.1')
      logging.info(u'{0:s} Bound to random port {1:d}'.format(
          self.name, self.port))

  def Start(self):
    """Starts this queue, causing the creation of a ZeroMQ socket.

    Raises:
      QueueAlreadyStarted: If the queue is already started, and a socket already
      exists.
    """
    if self._zmq_socket:
      raise QueueAlreadyStarted
    self._CreateZMQSocket()

  def Close(self, abort=False):
    """Closes the queue.

    Args:
      abort: If the Close is the result of an abort condition.

    Raises:
      QueueAlreadyClosed: If the queue is not started, or has already been
      closed.
    """
    if abort:
      self._linger_seconds = 0

    if not self._zmq_socket:
      # If we're aborting, things have already gone badly, so we won't throw
      # an additional exception.
      if abort:
        return
      raise QueueAlreadyClosed

    self._zmq_socket.close(self._linger_seconds)

  def Empty(self):
    """Empties all items from the queue."""
    return

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

  def Empty(self):
    """Empties the queue."""
    try:
      while True:
        if self._zmq_socket:
          self._zmq_socket.recv_pyobj()
    except zmq.error.Again:
      pass

  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      errors.QueueEmpty: If the queue is empty, and no item could be popped.
    """
    logging.debug(u'Pop on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
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
    logging.debug(u'Push on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()
    self._zmq_socket.send_pyobj(item)
