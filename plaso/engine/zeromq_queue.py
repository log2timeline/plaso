# -*- coding: utf-8 -*-
"""ZeroMQ implementations of the Plaso queue interface."""

import abc
import logging

import zmq

from plaso.engine import queue
from plaso.lib import errors


class ZeroMQQueue(queue.Queue):
  """Class that defines an interfaces for ZeroMQ backed Plaso queues.

  Attributes:
    port: The TCP port that the queue is connected or bound to. If the queue is
          not yet bound or connected to a port, this value will be None.
    name: A name to use to identify the queue.
  """

  _SOCKET_ADDRESS = u'tcp://127.0.0.1'
  _SOCKET_TYPE = None
  SOCKET_CONNECTION_BIND = 1
  SOCKET_CONNECTION_CONNECT = 2
  SOCKET_CONNECTION_TYPE = None

  def __init__(
      self, delay_start=True, linger_seconds=10, port=None, timeout_seconds=5,
      name=u'Unnamed'):
    """Initializes a ZeroMQ backed queue.

    Args:
      delay_start: Optional boolean that governs whether a ZeroMQ socket
                   should be created the first time the queue is pushed to or
                   popped from, rather than at queue object initialization.
                   This is useful if a queue needs to be passed to a
                   child process from a parent.
      linger_seconds: Optional number of seconds that the underlying ZeroMQ
                      socket can remain open after the queue object has been
                      closed, to allow queued items to be transferred to other
                      ZeroMQ sockets.
      port: The TCP port to use for the queue. The default is None, which
            indicates that the queue should choose a random port to bind to.
      timeout_seconds: Optional number of seconds that calls to PopItem and
                       PushItem may block for, before returning
                       queue.QueueEmpty.
      name: Optional name to identify the queue.

    Raises:
      AttributeError: If the queue is configured to connect to an endpoint,
                      but no port is specified.
    """
    if (self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT
        and not port):
      raise AttributeError(u'No port specified to connect to.')
    self._linger_seconds = linger_seconds
    self._timeout_milliseconds = timeout_seconds * 1000
    self._zmq_socket = None
    self.name = name
    self.port = port
    if not delay_start:
      self._CreateZMQSocket()

  @property
  def timeout_seconds(self):
    """Maximum number of seconds that calls to Pop or Push items can take."""
    return self._timeout_milliseconds / 1000

  @timeout_seconds.setter
  def timeout_seconds(self, value):
    """Maximum number of seconds that calls to Pop or Push items can take."""
    self._timeout_milliseconds = value * 1000
    self._SetSocketTimeouts()

  def _SetSocketTimeouts(self):
    """Sets the timeouts for socket send and receive."""
    if self._SOCKET_TYPE == zmq.PULL:
      self._zmq_socket.setsockopt(
          zmq.RCVTIMEO, self._timeout_milliseconds)
    elif self._SOCKET_TYPE == zmq.PUSH:
      self._zmq_socket.setsockopt(
          zmq.SNDTIMEO, self._timeout_milliseconds)

  def _CreateZMQSocket(self):
    """Creates a ZeroMQ socket."""
    zmq_context = zmq.Context()
    self._zmq_socket = zmq_context.socket(self._SOCKET_TYPE)
    self._SetSocketTimeouts()

    if self.port:
      address = u'{0:s}:{1:d}'.format(self._SOCKET_ADDRESS, self.port)
      if self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT:
        self._zmq_socket.connect(address)
        logging.debug(u'{0:s} Connected to {1:s}'.format(self.name, address))
      else:
        self._zmq_socket.bind(address)
        logging.debug(u'{0:s} Bound to specified port {1:s}'.format(
            self.name, address))
    else:
      self.port = self._zmq_socket.bind_to_random_port(self._SOCKET_ADDRESS)
      logging.debug(u'{0:s} Bound to random port {1:d}'.format(
          self.name, self.port))

  def Start(self):
    """Starts this queue, causing the creation of a ZeroMQ socket.

    Raises:
      QueueAlreadyStarted: If the queue is already started, and a socket already
      exists.
    """
    if self._zmq_socket:
      raise errors.QueueAlreadyStarted
    self._CreateZMQSocket()

  # pylint: disable=arguments-differ
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
      raise errors.QueueAlreadyClosed

    self._zmq_socket.close(self._linger_seconds)

  @abc.abstractmethod
  def Empty(self):
    """Empties all items from the queue."""

  def IsEmpty(self):
    """Checks if the queue is empty.

    ZeroMQ queues don't have a concept of "empty" - there could always be
    messages on the queue that a producer or consumer is unaware of. Thus,
    the queue is never empty, so we return False. Note that it is possible that
    a queue is unable to pop an item from a queue within a timeout, which will
    cause PopItem to return a QueueFull exception, but this is a slightly
    different condition.

    Returns:
      False
    """
    return False

  @abc.abstractmethod
  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Args:
      item: The item to push on the queue.
      block: Optional argument to indicate whether the push should be performed
             in blocking or non-block mode.
    """

  @abc.abstractmethod
  def PopItem(self):
    """Pops an item off the queue."""


class ZeroMQPullQueue(ZeroMQQueue):
  """Parent class for Plaso queues backed by ZeroMQ PULL sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to pop items, not to
  push.
  """

  _SOCKET_TYPE = zmq.PULL

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

    If no ZeroMQ socket has been created, one will be created the first
    time this method is called.

    Raises:
      QueueEmpty: If the queue is empty, and no item could be popped within the
                  queue timeout.
    """
    logging.debug(u'Pop on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()
    try:
      return self._zmq_socket.recv_pyobj()
    except zmq.error.Again:
      raise errors.QueueEmpty

  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Args:
      item: The item to push on to the queue.
      block: Optional argument to indicate whether the push should be performed
             in blocking or non-block mode.

    Raises:
      WrongQueueType: As Push is not supported this queue.
    """
    raise errors.WrongQueueType


class ZeroMQPullBindQueue(ZeroMQPullQueue):
  """A Plaso queue backed by a ZeroMQ PULL socket that binds to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQPullConnectQueue(ZeroMQPullQueue):
  """A Plaso queue backed by a ZeroMQ PULL socket that connects to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_CONNECT


class ZeroMQPushQueue(ZeroMQQueue):
  """Parent class for Plaso queues backed by ZeroMQ PUSH sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to push items, not to
  pop.
  """

  _SOCKET_TYPE = zmq.PUSH

  def PopItem(self):
    """Pops an item of the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Raises:
      WrongQueueType: As Pull is not supported this queue.
    """
    raise errors.WrongQueueType

  def PushItem(self, item, block=True):
    """Push an item on to the queue.

    If no ZeroMQ socket has been created, one will be created the first time
    this method is called.

    Args:
      item: The item to push on to the queue.
      block: Optional argument to indicate whether the push should be performed
             in blocking or non-block mode.

    Raises:
      QueueFull: If the push failed, due to the queue being full for the
                 duration of the timeout.
    """
    logging.debug(u'Push on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()
    try:
      if block:
        self._zmq_socket.send_pyobj(item)
      else:
        self._zmq_socket.send_pyobj(item, zmq.DONTWAIT)
    except zmq.error.Again:
      if block:
        raise errors.QueueFull

  def Empty(self):
    """Empties all items from the queue.

    Raises:
      WrongQueueType: As this queue type does not support emptying.
    """
    raise errors.WrongQueueType


class ZeroMQPushBindQueue(ZeroMQPushQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket that binds to a port.

  This queue may only be used to push items, not to pop.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND

class ZeroMQPushConnectQueue(ZeroMQPushQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket that connects to a port.

  This queue may only be used to push items, not to pop.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_CONNECT
