# -*- coding: utf-8 -*-
"""ZeroMQ implementations of the Plaso queue interface."""

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

  def __init__(
      self, connect=False, delay_start=True, linger_seconds=10,
      port=None, timeout_seconds=5, name=u'Unnamed'):
    """Initializes a ZeroMQ backed queue.

    Args:
      connect: Optional boolean that governs whether this queue should connect
               or bind to the given port. The default is False, which indicates
               that the queue should bind. If this argument is True, a value
               for the 'port' argument must be specified.
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
      name: Optional name used to identify the queue.

    Raises:
      AttributeError: If the queue is configured to connect to an endpoint,
                      but no port is specified.
    """
    if connect and not port:
      raise AttributeError(u'No port specified to connect to.')
    self._connect = connect
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
      address = u'{0:s}:{0:d}'.format(self._SOCKET_ADDRESS, self.port)
      if self._connect:
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

  def Empty(self):
    """Empties all items from the queue.

    Raises:
      NotImplementedError: If the implementing class does not support
                           emptying.
    """
    raise NotImplementedError

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

  def PushItem(self, item):
    """Pushes an item on to the queue.

    Args:
      item: The item to push on the queue.

    Raises:
      NotImplementedError: If Push is not supported by the implementing
                           class.
    """
    raise NotImplementedError

  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      NotImplementedError: If Pop is not supported by the implementing class.
    """
    raise NotImplementedError


class ZeroMQPullQueue(ZeroMQQueue):
  """A Plaso queue backed by a ZeroMQ PULL socket.

  This queue may only be used to pop items, not to push.
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

  def PushItem(self, item):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Args:
      item: The item to push on to the queue.

    Raises:
      NotImplementedError: As Push is not supported this queue.
    """
    raise NotImplementedError


class ZeroMQPushQueue(ZeroMQQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket.

  This queue may only be used to push items, not to pop.
  """

  _SOCKET_TYPE = zmq.PUSH

  def PopItem(self):
    """Pops an item of the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Raises:
      NotImplementedError: As Pull is not supported this queue.
    """
    raise NotImplementedError

  def PushItem(self, item):
    """Push an item on to the queue.

    If no ZeroMQ socket has been created, one will be created the first time
    this method is called.

    Args:
      item: The item to push on to the queue.

    Raises:
      QueueFull: If the push failed, due to the queue being full for the
                 duration of the timeout.
    """
    logging.debug(u'Push on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()
    try:
      self._zmq_socket.send_pyobj(item)
    except zmq.error.Again:
      raise errors.QueueFull
