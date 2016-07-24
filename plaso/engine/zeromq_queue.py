# -*- coding: utf-8 -*-
"""ZeroMQ implementations of the Plaso queue interface."""

import abc
import errno
import logging
import Queue
import threading
import time

import zmq

from plaso.engine import plaso_queue
from plaso.lib import errors


class _ZeroMQTimeoutHandler(object):
  """Class for handling timing out ZeroMQ operations"""

  def __init__(self, timeout_seconds, terminate_event=None):
    """Initializes a ZeroMQ timeout handler.

    This class allows short timeouts to be set for ZeroMQ, and control to be
    returned to Python code more frequently, so it can check the terminate flag..

    Args:
      timeout_seconds (int): maximum number of seconds to wait for the ZeroMQ
          operation to complete.
      terminate_event (Optional[threading.Event]): when set, indicates that the
          the operation should complete immediately.
    """
    super(_ZeroMQTimeoutHandler, self).__init__()
    self.latest_retry_timestamp = 0
    self._timeout_seconds = timeout_seconds
    self._terminate_event = terminate_event

  def __enter__(self):
    """Make usable with "with" statement."""
    self._latest_retry_timestamp = time.time() + self._timeout_seconds

  def __exit__(self, exception_type, unused_exception_value, exc_tb):
    """Make usable with "with" statement."""
    if exception_type is not zmq.error.Again:
      return False

    if self._terminate_event and self._terminate_event.isSet():
      logging.debug(u'Terminate event not set.')
      return False
    if time.time() > self._latest_retry_timestamp:
      logging.debug(
          u'{0:f} > {0:f}'.format(time.time(), self._latest_retry_timestamp))
      return False
    return True


class ZeroMQQueue(plaso_queue.Queue):
  """Class that defines an interfaces for ZeroMQ backed Plaso queues.

  Attributes:
    name (str): name to identify the queue.
    port (int): TCP port that the queue is connected or bound to. If the queue
        is not yet bound or connected to a port, this value will be None.
  """

  _SOCKET_ADDRESS = u'tcp://127.0.0.1'
  _SOCKET_TYPE = None
  SOCKET_CONNECTION_BIND = 1
  SOCKET_CONNECTION_CONNECT = 2
  SOCKET_CONNECTION_TYPE = None
  _ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS = 1000
  _ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS = 1000

  def __init__(
      self, delay_open=True, linger_seconds=10, port=None, timeout_seconds=5,
      name=u'Unnamed', maximum_items=1000):
    """Initializes a ZeroMQ backed queue.

    Args:
      delay_open (Optional[bool]): whether a ZeroMQ socket should be created
          the first time the queue is pushed to or popped from, rather than at
          queue object initialization. This is useful if a queue needs to be
          passed to a child process from a parent process.
      linger_seconds (Optional[int]): number of seconds that the underlying
          ZeroMQ socket can remain open after the queue object has been closed,
          to allow queued items to be transferred to other ZeroMQ sockets.
      port (Optional[int]): The TCP port to use for the queue. The default is None, which
            indicates that the queue should choose a random port to bind to.
      timeout_seconds (Optional[int]): number of seconds that calls to PopItem
          and PushItem may block for, before returning queue.QueueEmpty.
      name (Optional[str]): Optional name to identify the queue.
      maximum_items (Optional[int]): maximum number of items to queue on the
          ZeroMQ socket. ZeroMQ refers to this value as "high water mark" or
          "hwm". Note that this limit only applies at one "end" of the queue.
          The default of 1000 is the ZeroMQ default value.

    Raises:
      ValueError: If the queue is configured to connect to an endpoint,
                      but no port is specified.
    """
    if (self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT
        and not port):
      raise ValueError(u'No port specified to connect to.')
    self._closed = False
    self._high_water_mark = maximum_items
    self._linger_seconds = linger_seconds
    self.timeout_seconds = timeout_seconds
    self._terminate_event = threading.Event()
    self._zmq_context = None
    self._zmq_socket = None
    self._zmq_socket_timeout_milliseconds = 500
    self.name = name
    self.port = port
    if not delay_open:
      self._CreateZMQSocket()

  def _SetSocketTimeouts(self):
    """Sets the timeouts for socket send and receive."""
    self._zmq_socket.setsockopt(
        zmq.RCVTIMEO, self._ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS)
    self._zmq_socket.setsockopt(
        zmq.SNDTIMEO, self._ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS)

  def _SetSocketHighWaterMark(self):
    """Sets the high water mark for the socket.

    This number is the maximum number of items that will be queued on this end
    of the queue.
    """
    self._zmq_socket.hwm = self._high_water_mark

  def _CreateZMQSocket(self):
    """Creates a ZeroMQ socket."""
    logging.debug(u'Creating socket for {0:s}'.format(self.name))
    if not self._zmq_context:
      self._zmq_context = zmq.Context()
    if self._zmq_socket:
      self._zmq_socket.close(self._linger_seconds)
    self._zmq_socket = self._zmq_context.socket(self._SOCKET_TYPE)
    self._SetSocketTimeouts()
    self._SetSocketHighWaterMark()

    if self.port:
      address = u'{0:s}:{1:d}'.format(self._SOCKET_ADDRESS, self.port)
      if self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT:
        self._zmq_socket.connect(address)
        logging.debug(u'{0:s} connected to {1:s}'.format(self.name, address))
      else:
        self._zmq_socket.bind(address)
        logging.debug(u'{0:s} bound to specified port {1:s}'.format(
            self.name, address))
    else:
      self.port = self._zmq_socket.bind_to_random_port(self._SOCKET_ADDRESS)
      logging.debug(u'{0:s} bound to random port {1:d}'.format(
          self.name, self.port))

  def Open(self):
    """Opens this queue, causing the creation of a ZeroMQ socket.

    Raises:
      QueueAlreadyStarted: If the queue is already started, and a socket already
      exists.
    """
    if self._zmq_socket:
      raise errors.QueueAlreadyStarted()
    self._CreateZMQSocket()

  # pylint: disable=arguments-differ
  def Close(self, abort=False):
    """Closes the queue.

    Args:
      abort (bool): whether the Close is the result of an abort condition. If
          True, queue contents may be lost.

    Raises:
      QueueAlreadyClosed: If the queue is not started, or has already been
      closed.
    """
    if self._closed and not abort:
      raise errors.QueueAlreadyClosed()

    if abort:
      logging.warning(u'{0:s} queue aborting. Contents may be lost.'.format(
          self.name))
      try:
        self.Empty()
      except NotImplementedError:
        # Some queue types don't support this, but we're aborting, so we
        # ignore the error.
        pass
      self._linger_seconds = 0
    else:
      logging.debug(
          u'{0:s} queue closing, will linger for up to {1:d} seconds'.format(
              self.name, self._linger_seconds))

    self._closed = True
    # We can't determine whether a there might be an operation being performed
    # on the socket in a separate method or thread, so we'll signal that any
    # such operation should cease.
    self._terminate_event.set()

  @abc.abstractmethod
  def Empty(self):
    """Empties all items from the queue."""

  def IsBound(self):
    """Checks if the queue is bound to a port."""
    if (self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_BIND and
            self.port is not None):
      return True
    return False

  def IsConnected(self):
    """Checks if the queue is connected to a port."""
    if (self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT and
            self.port is not None):
      return True
    return False

  def IsEmpty(self):
    """Checks if the queue is empty.

    ZeroMQ queues don't have a concept of "empty" - there could always be
    messages on the queue that a producer or consumer is unaware of. Thus,
    the queue is never empty, so we return False. Note that it is possible that
    a queue is unable to pop an item from a queue within a timeout, which will
    cause PopItem to raise a QueueEmpty exception, but this is a different
    condition.

    Returns:
      bool: False, to indicate the the queue isn't empty.
    """
    return False

  @abc.abstractmethod
  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-block mode.

    Raises:
      QueueAlreadyClosed: If the queue is closed.
    """

  @abc.abstractmethod
  def PopItem(self):
    """Pops an item off the queue.

    Returns:
      object: item from the queue, or QueueAbort if no item could be retrieved
          within the timeout.

    Raises:
      QueueEmpty: If the queue is empty, and no item could be popped within the
                  queue timeout.
    """


class ZeroMQPullQueue(ZeroMQQueue):
  """Parent class for Plaso queues backed by ZeroMQ PULL sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to pop items, not to
  push.
  """

  _SOCKET_TYPE = zmq.PULL

  def Empty(self):
    """Empties the queue.

    Raises:
      zmq.error.ZMQError: If a ZeroMQ error occurs.
    """
    try:
      while True:
        if self._zmq_socket:
          self._zmq_socket.recv_pyobj()
    except zmq.error.Again:
      # Timeout dequeueing an item, so the queue is empty.
      pass
    except zmq.error.ZMQError as exception:
      if exception.errno == errno.EINTR:
        logging.error(u'ZMQ syscall interrupted in {0:s}.'.format(self.name))
        return
      else:
        raise

  def PopItem(self):
    """Pops an item off the queue.

    If no ZeroMQ socket has been created, one will be created the first
    time this method is called.

    Returns:
      object: item from the queue, or QueueAbort if no item could be retrieved
          within the timeout.

    Raises:
      QueueEmpty: If the queue is empty, and no item could be popped within the
                  queue timeout.
      zmq.error.ZMQError: If a ZeroMQ error occurs.
    """
    logging.debug(u'Pop on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()
    try:
      with _ZeroMQTimeoutHandler(self.timeout_seconds):
        return self._zmq_socket.recv_pyobj()
    except zmq.error.Again:
      return plaso_queue.QueueAbort()
    except zmq.error.ZMQError as exception:
      if exception.errno == errno.EINTR:
        logging.error(
            u'ZMQ syscall interrupted in {0:s}. Queue aborting'.format(
                self.name))
        return plaso_queue.QueueAbort()
      else:
        raise
    except KeyboardInterrupt:
      self.Close(abort=True)
      raise

  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-block mode.

    Raises:
      WrongQueueType: As Push is not supported this queue.
    """
    raise errors.WrongQueueType()


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
    raise errors.WrongQueueType()

  def PushItem(self, item, block=True):
    """Push an item on to the queue.

    If no ZeroMQ socket has been created, one will be created the first time
    this method is called.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-block mode.

    Raises:
      KeyboardInterrupt: If the process is sent a KeyboardInterrupt while
                         pushing an item.
      zmq.error.Again: If it was not possible to push the item to the queue
                       within the timeout.
      zmq.error.ZMQError: If a ZeroMQ specific error occurs.
    """
    logging.debug(u'Push on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()
    try:
      if block:
        with _ZeroMQTimeoutHandler(self.timeout_seconds):
          self._zmq_socket.send_pyobj(item)
      else:
        self._zmq_socket.send_pyobj(item, zmq.DONTWAIT)
    except zmq.error.Again:
      logging.error(u'{0:s} unable to push item, raising.'.format(self.name))
      raise errors.QueueEmpty
    except zmq.error.ZMQError as exception:
      if exception.errno == errno.EINTR:
        logging.error(u'ZMQ syscall interrupted in {0:s}.'.format(self.name))
        return plaso_queue.QueueAbort()
      else:
        raise
    except KeyboardInterrupt:
      self.Close(abort=True)
      raise

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


class ZeroMQRequestQueue(ZeroMQQueue):
  """Parent class for Plaso queues backed by ZeroMQ REQ sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to pop items, not to
  push.
  """

  _SOCKET_TYPE = zmq.REQ

  _ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS = 2000
  _ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS = 2000


  def Empty(self):
    """Empties the queue.

    Raises:
      zmq.error.ZMQError: If an error occurs in ZeroMQ.
    """
    try:
      while True:
        if self._zmq_socket:
          self._zmq_socket.send_pyobj(None)
          self._zmq_socket.recv_pyobj()
    except zmq.error.Again:
      # Timeout receiving on queue, so we can conclude that the queue is empty.
      return
    except zmq.error.ZMQError as exception:
      if exception.errno == errno.EINTR:
        # Interrupted syscall, we won't be able to dequeue any more items from
        # this queue, so we can consider it empty.
        logging.error(u'ZMQ syscall interrupted in {0:s}.'.format(self.name))
        return
      else:
        raise

  def PopItem(self):
    """Pops an item off the queue.

    If no ZeroMQ socket has been created, one will be created the first
    time this method is called.

    Returns:
      object: item from the queue, or QueueAbort if no item could be retrieved
          within the timeout.

    Raises:
      KeyboardInterrupt: If the process is sent a KeyboardInterrupt while
                         popping an item.
      QueueEmpty: If the queue is empty, and no item could be popped within the
                  queue timeout.
      zmq.error.ZMQError: If an error occurs in ZeroMQ.

    """
    logging.debug(u'Pop on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()

    last_retry_time = time.time() + self.timeout_seconds
    while not self._terminate_event.isSet():
      try:
        logging.debug(u'{0:s} Sending request'.format(self.name))
        self._zmq_socket.send_pyobj(None)
      except zmq.error.Again:
        if time.time() > last_retry_time:
          logging.warn(u'{0:s} timeout requesting item'.format(self.name))
          raise errors.QueueEmpty

        # The existing socket is now out of sync, so we need to open a new one.
        self._CreateZMQSocket()
        continue
      except zmq.error.ZMQError as exception:
        if exception.errno == errno.EINTR:
          logging.error(
              u'{0:s} ZMQ syscall interrupted. Queue aborting.'.format(
                  self.name))
          return plaso_queue.QueueAbort()
        if exception.errno == zmq.EFSM:
          if time.time() > last_retry_time:
            logging.warn(
                u'{0:s} time out sending request for item'.format(self.name))
            raise errors.QueueEmpty
          self._CreateZMQSocket()
          continue

        raise
      except KeyboardInterrupt:
        self.Close(abort=True)
        raise

      try:
        logging.debug(u'{0:s} receiving object.'.format(
            self.name,))
        received_object = self._zmq_socket.recv_pyobj()
        logging.debug(u'{0:s} received object: "{1:s}"'.format(
            self.name, received_object))
        return received_object
      except zmq.error.Again:
        if time.time() > last_retry_time:
          raise errors.QueueEmpty

        # The existing socket is now out of sync, so we need to open a new one
        # and make another request.
        self._CreateZMQSocket()
        continue
      except zmq.error.ZMQError as exception:
        if exception.errno == errno.EINTR:
          logging.error(
              u'ZMQ syscall interrupted in {0:s}. Queue aborting.'.format(
                  self.name))
          return plaso_queue.QueueAbort()

        raise

      except KeyboardInterrupt:
        self.Close(abort=True)
        raise

  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-block mode.

    Raises:
      WrongQueueType: As Push is not supported this queue.
    """
    raise errors.WrongQueueType


class ZeroMQRequestBindQueue(ZeroMQRequestQueue):
  """A Plaso queue backed by a ZeroMQ REQ socket that binds to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQRequestConnectQueue(ZeroMQRequestQueue):
  """A Plaso queue backed by a ZeroMQ REQ socket that connects to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_CONNECT


class ZeroMQBufferedQueue(ZeroMQQueue):
  """Parent class for buffered Plaso queues..

  This class should not be instantiated directly, a subclass should be
  instantiated instead.
  """

  def __init__(
      self, delay_open=True, linger_seconds=10, port=None, timeout_seconds=5,
      name=u'Unnamed', maximum_items=1000, buffer_max_size=10000,
      buffer_timeout_seconds=2):
    """Initializes a buffered, ZeroMQ backed queue.

    Args:
      delay_open (Optional[bool]): whether a ZeroMQ socket should be created
          the first time the queue is pushed to or popped from, rather than at
          queue object initialization. This is useful if a queue needs to be
          passed to a child process from a parent process.
      linger_seconds (Optional[int]): number of seconds that the underlying
          ZeroMQ socket can remain open after the queue object has been closed,
          to allow queued items to be transferred to other ZeroMQ sockets.
      port (Optional[int]): The TCP port to use for the queue. None indicates
          that the queue should choose a random port to bind to.
      timeout_seconds (Optional[int]): number of seconds that calls to PopItem
          and PushItem may block for, before returning queue.QueueEmpty.
      name (Optional[str]): name to identify the queue.
      maximum_items (Optional[int]): maximum number of items to queue on the
          ZeroMQ socket. ZeroMQ refers to this value as "high water mark" or
          "hwm". Note that this limit only applies at one "end" of the queue.
          The default of 1000 is the ZeroMQ default value.
      buffer_max_size (Optional[int]): maximum number of items to store in
          the buffer, before or after they are sent/received via ZeroMQ.
      buffer_timeout_seconds(Optional[int]): number of seconds to wait when
          doing a put or get to/from the internal buffer.
    """
    self._buffer_timeout_seconds = buffer_timeout_seconds
    self._queue = Queue.Queue(maxsize=buffer_max_size)
    # We need to set up the internal buffer queue before we call super, so that
    # if the call to super opens the ZMQSocket, the backing thread will work.
    super(ZeroMQBufferedQueue, self).__init__(
        delay_open, linger_seconds, port, timeout_seconds, name,
        maximum_items)

  def _CreateZMQSocket(self):
    """Creates a ZeroMQ socket as well as a regular queue and a thread."""
    super(ZeroMQBufferedQueue, self)._CreateZMQSocket()
    thread_name = u'{0:s}_zmq_responder'.format(self.name)
    self._zmq_thread = threading.Thread(
        target=self._ZeroMQResponder, args=(
          self._queue, self._zmq_socket, self._terminate_event),
        name=thread_name)
    self._zmq_thread.start()

  @abc.abstractmethod
  def _ZeroMQResponder(self, source_queue, socket, terminate_event):
    """Listens for requests and replies to clients.

    Args:
      source_queue (Queue.queue): queue to to pull items from.
      socket (zmq.Socket): socket to listen on, and send responses to.
      terminate_event (Queue.Event): event that signals that the queue should
          terminate.
    """

  # pylint: disable=arguments-differ
  def Close(self, abort=False):
    """Closes the queue.

    Args:
      abort (bool): whether the Close is the result of an abort condition. If
          True, queue contents may be lost.

    Raises:
      QueueAlreadyClosed: If the queue is not started, or has already been
      closed.
    """
    if self._closed and not abort:
      raise errors.QueueAlreadyClosed()

    if abort:
      logging.warning(u'{0:s} queue aborting. Contents may be lost.'.format(
          self.name))
      try:
        self.Empty()
      except NotImplementedError:
        # Some queue types don't support this, but we're aborting, so we
        # ignore the error.
        pass
      self._linger_seconds = 0
    else:
      logging.debug(
          u'{0:s} queue closing, will linger for up to {1:d} seconds'.format(
              self.name, self._linger_seconds))

    self._closed = True
    # We can't determine whether a there might be an operation being performed
    # on the socket in a separate method or thread, so we'll signal that any
    # such operation should cease.
    self._terminate_event.set()
    if self._zmq_thread:
      logging.debug(u'[{0:s}] Waiting for thread to exit.'.format(self.name))
      self._zmq_thread.join(timeout=self.timeout_seconds)

  def Empty(self):
    """Empty the queue."""
    while not self._queue.empty():
      self._queue.get_nowait()


class ZeroMQBufferedReplyQueue(ZeroMQBufferedQueue):
  """Parent class for buffered Plaso queues backed by ZeroMQ REP sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to push items, not to
  pop.
  """

  _ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS = 5000
  _ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS = 2000

  _SOCKET_TYPE = zmq.REP

  def _ZeroMQResponder(self, source_queue, socket, terminate_event):
    """Listens for requests and replies to clients.

    Args:
      source_queue: The queue to uses to pull items from.
      socket: The socket to listen on, and send responses to.
      terminate_event: The event that signals that the queue should terminate.

    Raises:
      QueueEmpty: If a timeout occurs when trying to reply to a request.
      zmq.error.ZMQError: If an error occurs in ZeroMQ.
    """
    logging.debug(u'{0:s} responder thread started'.format(self.name))
    last_retry_time = None
    while not terminate_event.isSet():
      if not last_retry_time:
        last_retry_time = time.time() + self.timeout_seconds
      try:
        # We need to receive a request before we send.
        _ = socket.recv()
      except zmq.error.Again:
        if time.time() > last_retry_time:
          logging.debug(
              u'{0:s} did not receive a request within the timeout of {1:d} '
              u'seconds. Queue terminating'.format(
                  self.name, self.timeout_seconds))
          self._terminate_event.set()
          break
        # The socket is now out of sync, so we need to create a new one.
        self._CreateZMQSocket()
        continue
      except zmq.error.ZMQError as exception:
        if exception.errno == errno.EINTR:
          logging.error(u'ZMQ syscall interrupted in {0:s}.'.format(self.name))
          break
        logging.debug(u'{0:s} zmq exception'.format(self.name))
        raise

      try:
        if self._closed:
          logging.debug(u'{0:s} getting item'.format(self.name))
          item = source_queue.get_nowait()
        else:
          logging.debug(u'{0:s} waiting for item'.format(self.name))
          item = source_queue.get(True, self._buffer_timeout_seconds)
      except Queue.Empty:
        logging.debug(u'{0:s} queue was empty'.format(self.name))
        item = plaso_queue.QueueAbort()

      try:
        logging.debug(u'{0:s} sending item'.format(self.name))
        self._zmq_socket.send_pyobj(item)
        logging.debug(u'{0:s} sent item'.format(self.name))
      except zmq.error.Again:
        logging.debug(
            u'{0:s} could not reply to a request.'.format(self.name))
        raise errors.QueueEmpty
      except zmq.error.ZMQError as exception:
        if exception.errno == errno.EINTR:
          logging.error(u'ZMQ syscall interrupted in {0:s}.'.format(self.name))
          break
        raise
    logging.info(u'Queue {0:s} responder exiting.'.format(self.name))
    socket.close(self._linger_seconds)

  def PopItem(self):
    """Pops an item of the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Raises:
      WrongQueueType: As Pop is not supported by this queue.
    """
    raise errors.WrongQueueType()

  def PushItem(self, item, block=True):
    """Push an item on to the queue.

    If no ZeroMQ socket has been created, one will be created the first time
    this method is called.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-block mode.

    Raises:
      QueueAlreadyClosed: If the queue is closed.
    """
    logging.debug(u'Pushing {0!s} to queue'.format(item))
    if self._closed:
      raise errors.QueueAlreadyClosed()
    if not self._zmq_socket:
      self._CreateZMQSocket()
    if block:
      self._queue.put(item, timeout=self._buffer_timeout_seconds)
    else:
      self._queue.put(item, block=False)


class ZeroMQBufferedReplyBindQueue(ZeroMQBufferedReplyQueue):
  """A Plaso queue backed by a ZeroMQ REP socket that binds to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQBufferedReplyConnectQueue(ZeroMQBufferedReplyQueue):
  """A Plaso queue backed by a ZeroMQ REP socket that connects to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_CONNECT


class ZeroMQBufferedPushQueue(ZeroMQBufferedQueue):
  """Parent class for buffered Plaso queues backed by ZeroMQ PUSH sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to push items, not to
  pop.
  """

  _SOCKET_TYPE = zmq.PUSH

  def _ZeroMQResponder(self, source_queue, socket, terminate_event):
    """Listens for requests and replies to clients.

    Args:
      source_queue: The queue to uses to pull items from.
      socket: The socket to listen to, and send responses to.
      terminate_event: The event that signals that the queue should terminate.

    Raises:
      QueueEmpty: If the queue encountered a timeout trying to push an item.
      zmq.error.ZMQError: If ZeroMQ encounters an error.
    """
    logging.debug(u'{0:s} responder thread started'.format(self.name))
    while not terminate_event.isSet():
      try:
        if self._closed:
          # No further items can be added be added to the queue, so we don't
          # need to block.
          item = source_queue.get_nowait()
        else:
          item = source_queue.get(True, timeout=self._buffer_timeout_seconds)
      except Queue.Empty:
        # No item available within timeout, so time to exit.
        break

      try:
        with _ZeroMQTimeoutHandler(
            self.timeout_seconds, terminate_event=terminate_event):
          self._zmq_socket.send_pyobj(item)
      except zmq.error.Again:
        logging.debug(
            u'{0:s} could not push an item within {1:d} seconds.'.format(
                self.name, self.timeout_seconds))
        raise errors.QueueEmpty
      except zmq.error.ZMQError as exception:
        if exception.errno == errno.EINTR:
          logging.error(u'ZMQ syscall interrupted in {0:s}.'.format(self.name))
          break
        else:
          raise
    logging.info(u'Queue {0:s} responder exiting.'.format(self.name))
    self._zmq_socket.close(self._linger_seconds)

  def PushItem(self, item, block=True):
    """Push an item on to the queue.

    If no ZeroMQ socket has been created, one will be created the first time
    this method is called.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-block mode.

    Raises:
      QueueAlreadyClosed: If there is an attempt to close a queue that's already
        closed.
    """
    if self._closed:
      raise errors.QueueAlreadyClosed()
    if not self._zmq_socket:
      self._CreateZMQSocket()
    self._queue.put(item, block=block, timeout=self._buffer_timeout_seconds)

  def PopItem(self):
    """Pops an item off the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Raises:
      WrongQueueType: As Pop is not supported by this queue.
    """
    raise errors.WrongQueueType


class ZeroMQBufferedPushBindQueue(ZeroMQBufferedPushQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket that binds to a port.

  This queue may only be used to push items, not to pop.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQBufferedPushConnectQueue(ZeroMQBufferedPushQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket that connects to a port.

  This queue may only be used to push items, not to pop.
  """

  _ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS = 5000

  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_CONNECT


class ZeroMQBufferedPullQueue(ZeroMQBufferedQueue):
  """Parent class for buffered Plaso queues backed by ZeroMQ PULL sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to pop items, not to
  push.
  """

  _SOCKET_TYPE = zmq.PULL
  _DOWNSTREAM_QUEUE_MAX_TRIES = 10
  _DOWNSTREAM_QUEUE_SLEEP_TIME = 0.2

  def _ZeroMQResponder(self, source_queue, socket, terminate_event):
    """Listens for requests and replies to clients.

    Args:
      source_queue: The queue to uses to pull items from.
      socket: The socket to listen to, and send responses to.
      terminate_event: The event that signals that the queue should terminate.

    Raises:
      zmq.error.ZMQError: If an error is encountered by ZeroMQ.
    """
    logging.debug(u'{0:s} responder thread started'.format(self.name))
    while not terminate_event.isSet():
      item = plaso_queue.QueueAbort()
      try:
        with _ZeroMQTimeoutHandler(
            timeout_seconds=self.timeout_seconds,
            terminate_event=terminate_event):
          item = socket.recv_pyobj()
      except zmq.error.Again:
        # No item received within timeout.
        logging.warn(u'{0:s} aborting, no item received in time.'.format(
            self.name))
      except zmq.error.ZMQError as exception:
        if exception.errno == errno.EINTR:
          logging.error(u'ZMQ syscall interrupted in {0:s}.'.format(self.name))
          break
        else:
          raise
      retries = 0
      while retries < self._DOWNSTREAM_QUEUE_MAX_TRIES:
        try:
          self._queue.put(item, timeout=self._buffer_timeout_seconds)
          break
        except Queue.Full:
          logging.debug(u'Queue {0:s} buffer limit hit.'.format(self.name))
          retries += 1
          if retries >= self._DOWNSTREAM_QUEUE_MAX_TRIES:
            logging.error(
                u'{0:s} buffer queue full for too long, aborting'.format(
                    self.name))
            break
          else:
            time.sleep(self._DOWNSTREAM_QUEUE_SLEEP_TIME)
            continue
    logging.info(u'Queue {0:s} responder exiting.'.format(self.name))
    self._zmq_socket.close(self._linger_seconds)

  def PopItem(self):
    """Pops an item off the queue.

    If no ZeroMQ socket has been created, one will be created the first
    time this method is called.

    Returns:
      object: item from the queue, or QueueAbort if no item could be retrieved
          within the timeout.

    Raises:
      QueueEmpty: If the queue is empty, and no item could be popped within the
                  queue timeout.
      zmq.error.ZMQError: If an error is encountered by ZeroMQ.
    """
    logging.debug(u'Pop on {0:s} queue, port {1:d}'.format(
        self.name, self.port))
    if not self._zmq_socket:
      self._CreateZMQSocket()
    try:
      return self._queue.get(timeout=self._buffer_timeout_seconds)
    except Queue.Empty:
      return plaso_queue.QueueAbort()
    except KeyboardInterrupt:
      self.Close(abort=True)
      raise

  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-block mode.

    Raises:
      WrongQueueType: As Push is not supported this queue.
    """
    raise errors.WrongQueueType()


class ZeroMQBufferedPullBindQueue(ZeroMQBufferedPullQueue):
  """A Plaso queue backed by a ZeroMQ PULL socket that binds to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQBufferedPullConnectQueue(ZeroMQBufferedPullQueue):
  """A Plaso queue backed by a ZeroMQ PULL socket that connects to a port.

  This queue may only be used to pop items, not to push.
  """

  _ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS = 5000

  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_CONNECT
