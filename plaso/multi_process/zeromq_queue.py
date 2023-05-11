# -*- coding: utf-8 -*-
"""ZeroMQ implementations of the Plaso queue interface."""

import abc
import errno
import queue
import threading
import time

import zmq

from plaso.engine import logger
from plaso.lib import errors
from plaso.multi_process import plaso_queue


# pylint: disable=no-member

class ZeroMQQueue(plaso_queue.Queue):
  """Interface for a ZeroMQ backed queue.

  Attributes:
    name (str): name to identify the queue.
    port (int): TCP port that the queue is connected or bound to. If the queue
        is not yet bound or connected to a port, this value will be None.
    timeout_seconds (int): number of seconds that calls to PopItem and PushItem
        may block for, before returning queue.QueueEmpty.
  """

  _SOCKET_ADDRESS = 'tcp://127.0.0.1'
  _SOCKET_TYPE = None

  _ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS = 1500
  _ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS = 1500

  SOCKET_CONNECTION_BIND = 1
  SOCKET_CONNECTION_CONNECT = 2
  SOCKET_CONNECTION_TYPE = None

  def __init__(
      self, delay_open=True, linger_seconds=10, maximum_items=1000,
      name='Unnamed', port=None, timeout_seconds=5):
    """Initializes a ZeroMQ backed queue.

    Args:
      delay_open (Optional[bool]): whether a ZeroMQ socket should be created
          the first time the queue is pushed to or popped from, rather than at
          queue object initialization. This is useful if a queue needs to be
          passed to a child process from a parent process.
      linger_seconds (Optional[int]): number of seconds that the underlying
          ZeroMQ socket can remain open after the queue has been closed,
          to allow queued items to be transferred to other ZeroMQ sockets.
      maximum_items (Optional[int]): maximum number of items to queue on the
          ZeroMQ socket. ZeroMQ refers to this value as "high water mark" or
          "hwm". Note that this limit only applies at one "end" of the queue.
          The default of 1000 is the ZeroMQ default value.
      name (Optional[str]): Optional name to identify the queue.
      port (Optional[int]): The TCP port to use for the queue. The default is
          None, which indicates that the queue should choose a random port to
          bind to.
      timeout_seconds (Optional[int]): number of seconds that calls to PopItem
          and PushItem may block for, before returning queue.QueueEmpty.

    Raises:
      ValueError: if the queue is configured to connect to an endpoint,
          but no port is specified.
    """
    if (self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT
        and not port):
      raise ValueError('No port specified to connect to.')

    super(ZeroMQQueue, self).__init__()
    self._closed_event = None
    self._high_water_mark = maximum_items
    self._linger_seconds = linger_seconds
    self._terminate_event = None
    self._zmq_context = None
    self._zmq_socket = None

    self.name = name
    self.port = port
    self.timeout_seconds = timeout_seconds

    if not delay_open:
      self._CreateZMQSocket()

  def _SendItem(self, zmq_socket, item, block=True):
    """Attempts to send an item to a ZeroMQ socket.

    Args:
      zmq_socket (zmq.Socket): used to the send the item.
      item (object): sent on the queue. Will be pickled prior to sending.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-blocking mode.

    Returns:
      bool: whether the item was sent successfully.
    """
    try:
      logger.debug('{0:s} sending item'.format(self.name))
      if block:
        zmq_socket.send_pyobj(item)
      else:
        zmq_socket.send_pyobj(item, zmq.DONTWAIT)
      logger.debug('{0:s} sent item'.format(self.name))
      return True

    except zmq.error.Again:
      logger.debug('{0:s} could not send an item'.format(self.name))

    except zmq.error.ZMQError as exception:
      if exception.errno == errno.EINTR:
        logger.error(
            'ZMQ syscall interrupted in {0:s}.'.format(
                self.name))

    return False

  def _ReceiveItemOnActivity(self, zmq_socket):
    """Attempts to receive an item from a ZeroMQ socket.

    Args:
      zmq_socket (zmq.Socket): used to the receive the item.

    Returns:
      object: item from the socket.

    Raises:
      QueueEmpty: if no item could be received within the timeout.
      zmq.error.ZMQError: if an error occurs in ZeroMQ
    """
    events = zmq_socket.poll(
        self._ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS)
    if events:
      try:
        received_object = self._zmq_socket.recv_pyobj()
        return received_object

      except zmq.error.Again:
        logger.error(
            '{0:s}. Failed to receive item in time.'.format(
                self.name))
        raise

      except zmq.error.ZMQError as exception:
        if exception.errno == errno.EINTR:
          logger.error(
              'ZMQ syscall interrupted in {0:s}. Queue aborting.'.format(
                  self.name))
        raise

    raise errors.QueueEmpty

  def _SetSocketTimeouts(self):
    """Sets the timeouts for socket send and receive."""
    # Note that timeout must be an integer value. If timeout is a float
    # it appears that zmq will not enforce the timeout.
    timeout = int(self.timeout_seconds * 1000)
    receive_timeout = min(
        self._ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS, timeout)
    send_timeout = min(self._ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS, timeout)

    self._zmq_socket.setsockopt(zmq.RCVTIMEO, receive_timeout)
    self._zmq_socket.setsockopt(zmq.SNDTIMEO, send_timeout)

  def _SetSocketHighWaterMark(self):
    """Sets the high water mark for the socket.

    This number is the maximum number of items that will be queued in the socket
    on this end of the queue.
    """
    self._zmq_socket.hwm = self._high_water_mark

  def _CreateZMQSocket(self):
    """Creates a ZeroMQ socket."""
    logger.debug('Creating socket for {0:s}'.format(self.name))

    if not self._zmq_context:
      self._zmq_context = zmq.Context()  # pylint: disable=abstract-class-instantiated

    # The terminate and close threading events need to be created when the
    # socket is opened. Threading events are unpickleable objects and cannot
    # passed in multiprocessing on Windows.

    if not self._terminate_event:
      self._terminate_event = threading.Event()

    if not self._closed_event:
      self._closed_event = threading.Event()

    if self._zmq_socket:
      logger.debug('Closing old socket for {0:s}'.format(self.name))
      self._zmq_socket.close()
      self._zmq_socket = None

    self._zmq_socket = self._zmq_context.socket(self._SOCKET_TYPE)
    self._SetSocketTimeouts()
    self._SetSocketHighWaterMark()

    if self.port:
      address = '{0:s}:{1:d}'.format(self._SOCKET_ADDRESS, self.port)
      if self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT:
        self._zmq_socket.connect(address)
        logger.debug('{0:s} connected to {1:s}'.format(self.name, address))
      else:
        self._zmq_socket.bind(address)
        logger.debug(
            '{0:s} bound to specified port {1:s}'.format(self.name, address))
    else:
      self.port = self._zmq_socket.bind_to_random_port(self._SOCKET_ADDRESS)
      logger.debug(
          '{0:s} bound to random port {1:d}'.format(self.name, self.port))

  def Open(self):
    """Opens this queue, causing the creation of a ZeroMQ socket.

    Raises:
      QueueAlreadyStarted: if the queue is already started, and a socket already
          exists.
    """
    if self._zmq_socket:
      raise errors.QueueAlreadyStarted()

    self._CreateZMQSocket()

  def Close(self, abort=False):
    """Closes the queue.

    Args:
      abort (Optional[bool]): whether the Close is the result of an abort
          condition. If True, queue contents may be lost.

    Raises:
      QueueAlreadyClosed: if the queue is not started, or has already been
          closed.
      RuntimeError: if closed or terminate event is missing.
    """
    if not self._closed_event or not self._terminate_event:
      raise RuntimeError('Missing closed or terminate event.')

    if not abort and self._closed_event.is_set():
      raise errors.QueueAlreadyClosed()

    self._closed_event.set()

    if abort:
      if not self._closed_event.is_set():
        logger.warning(
            '{0:s} queue aborting. Contents may be lost.'.format(self.name))

      self._linger_seconds = 0

      # We can't determine whether a there might be an operation being performed
      # on the socket in a separate method or thread, so we'll signal that any
      # such operation should cease.
      self._terminate_event.set()

    else:
      logger.debug(
          '{0:s} queue closing, will linger for up to {1:d} seconds'.format(
              self.name, self._linger_seconds))

  def IsBound(self):
    """Checks if the queue is bound to a port."""
    return (self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_BIND and
            self.port is not None)

  def IsConnected(self):
    """Checks if the queue is connected to a port."""
    return (self.SOCKET_CONNECTION_TYPE == self.SOCKET_CONNECTION_CONNECT and
            self.port is not None)

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
          or non-blocking mode.

    Raises:
      QueueAlreadyClosed: if the queue is closed.
    """

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def PopItem(self):
    """Pops an item off the queue.

    Returns:
      object: item from the queue.

    Raises:
      QueueEmpty: if the queue is empty, and no item could be popped within the
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

  def PopItem(self):
    """Pops an item off the queue.

    If no ZeroMQ socket has been created, one will be created the first
    time this method is called.

    Returns:
      object: item from the queue.

    Raises:
      KeyboardInterrupt: if the process is sent a KeyboardInterrupt while
          popping an item.
      QueueEmpty: if the queue is empty, and no item could be popped within the
          queue timeout.
      RuntimeError: if closed or terminate event is missing.
      zmq.error.ZMQError: if a ZeroMQ error occurs.
    """
    if not self._zmq_socket:
      self._CreateZMQSocket()

    if not self._closed_event or not self._terminate_event:
      raise RuntimeError('Missing closed or terminate event.')

    logger.debug(
        'Pop on {0:s} queue, port {1:d}'.format(self.name, self.port))

    last_retry_timestamp = time.time() + self.timeout_seconds
    while not self._closed_event.is_set() or not self._terminate_event.is_set():
      try:
        return self._ReceiveItemOnActivity(self._zmq_socket)

      except errors.QueueEmpty:
        if time.time() > last_retry_timestamp:
          raise

      except KeyboardInterrupt:
        self.Close(abort=True)
        raise

    return None

  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-blocking mode.

    Raises:
      WrongQueueType: As Push is not supported this queue.
    """
    raise errors.WrongQueueType()


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
          or non-blocking mode.

    Raises:
      KeyboardInterrupt: if the process is sent a KeyboardInterrupt while
          pushing an item.
      QueueFull: if it was not possible to push the item to the queue
          within the timeout.
      RuntimeError: if terminate event is missing.
      zmq.error.ZMQError: if a ZeroMQ specific error occurs.
    """
    if not self._zmq_socket:
      self._CreateZMQSocket()

    if not self._terminate_event:
      raise RuntimeError('Missing terminate event.')

    logger.debug(
        'Push on {0:s} queue, port {1:d}'.format(self.name, self.port))

    last_retry_timestamp = time.time() + self.timeout_seconds
    while not self._terminate_event.is_set():
      try:
        send_successful = self._SendItem(self._zmq_socket, item, block)
        if send_successful:
          break

        if time.time() > last_retry_timestamp:
          logger.error('{0:s} unable to push item, raising.'.format(
              self.name))
          raise errors.QueueFull

      except KeyboardInterrupt:
        self.Close(abort=True)
        raise


class ZeroMQPushBindQueue(ZeroMQPushQueue):
  """A Plaso queue backed by a ZeroMQ PUSH socket that binds to a port.

  This queue may only be used to push items, not to pop.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND


class ZeroMQRequestQueue(ZeroMQQueue):
  """Parent class for Plaso queues backed by ZeroMQ REQ sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to pop items, not to
  push.
  """

  _SOCKET_TYPE = zmq.REQ

  def PopItem(self):
    """Pops an item off the queue.

    If no ZeroMQ socket has been created, one will be created the first
    time this method is called.

    Returns:
      object: item from the queue.

    Raises:
      KeyboardInterrupt: if the process is sent a KeyboardInterrupt while
          popping an item.
      QueueEmpty: if the queue is empty, and no item could be popped within the
          queue timeout.
      RuntimeError: if terminate event is missing.
      zmq.error.ZMQError: if an error occurs in ZeroMQ.
    """
    if not self._zmq_socket:
      self._CreateZMQSocket()

    if not self._terminate_event:
      raise RuntimeError('Missing terminate event.')

    logger.debug('Pop on {0:s} queue, port {1:d}'.format(
        self.name, self.port))

    last_retry_time = time.time() + self.timeout_seconds
    while not self._terminate_event.is_set():
      try:
        self._zmq_socket.send_pyobj(None)
        break

      except zmq.error.Again:
        # The existing socket is now out of sync, so we need to open a new one.
        self._CreateZMQSocket()
        if time.time() > last_retry_time:
          logger.warning('{0:s} timeout requesting item'.format(self.name))
          raise errors.QueueEmpty

        continue

    while not self._terminate_event.is_set():
      try:
        return self._ReceiveItemOnActivity(self._zmq_socket)
      except errors.QueueEmpty:
        continue

      except KeyboardInterrupt:
        self.Close(abort=True)
        raise

    return None

  def PushItem(self, item, block=True):
    """Pushes an item on to the queue.

    Provided for compatibility with the API, but doesn't actually work.

    Args:
      item (object): item to push on the queue.
      block (Optional[bool]): whether the push should be performed in blocking
          or non-blocking mode.

    Raises:
      WrongQueueType: As Push is not supported this queue.
    """
    raise errors.WrongQueueType


class ZeroMQRequestConnectQueue(ZeroMQRequestQueue):
  """A Plaso queue backed by a ZeroMQ REQ socket that connects to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_CONNECT


class ZeroMQBufferedQueue(ZeroMQQueue):
  """Parent class for buffered Plaso queues.

  Buffered queues use a regular Python queue to store items that are pushed or
  popped from the queue without blocking on underlying ZeroMQ operations.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.
  """

  def __init__(
      self, buffer_timeout_seconds=2, buffer_max_size=10000, delay_open=True,
      linger_seconds=10, maximum_items=1000, name='Unnamed', port=None,
      timeout_seconds=5):
    """Initializes a buffered, ZeroMQ backed queue.

    Args:
      buffer_max_size (Optional[int]): maximum number of items to store in
          the buffer, before or after they are sent/received via ZeroMQ.
      buffer_timeout_seconds(Optional[int]): number of seconds to wait when
          doing a put or get to/from the internal buffer.
      delay_open (Optional[bool]): whether a ZeroMQ socket should be created
          the first time the queue is pushed to or popped from, rather than at
          queue object initialization. This is useful if a queue needs to be
          passed to a child process from a parent process.
      linger_seconds (Optional[int]): number of seconds that the underlying
          ZeroMQ socket can remain open after the queue object has been closed,
          to allow queued items to be transferred to other ZeroMQ sockets.
      maximum_items (Optional[int]): maximum number of items to queue on the
          ZeroMQ socket. ZeroMQ refers to this value as "high water mark" or
          "hwm". Note that this limit only applies at one "end" of the queue.
          The default of 1000 is the ZeroMQ default value.
      name (Optional[str]): name to identify the queue.
      port (Optional[int]): The TCP port to use for the queue. None indicates
          that the queue should choose a random port to bind to.
      timeout_seconds (Optional[int]): number of seconds that calls to PopItem
          and PushItem may block for, before returning queue.QueueEmpty.
    """
    self._buffer_timeout_seconds = buffer_timeout_seconds
    self._queue = queue.Queue(maxsize=buffer_max_size)
    self._zmq_thread = None

    # We need to set up the internal buffer queue before we call super, so that
    # if the call to super opens the ZMQSocket, the backing thread will work.
    super(ZeroMQBufferedQueue, self).__init__(
        delay_open=delay_open, linger_seconds=linger_seconds,
        maximum_items=maximum_items, name=name, port=port,
        timeout_seconds=timeout_seconds)

  def _CreateZMQSocket(self):
    """Creates a ZeroMQ socket as well as a regular queue and a thread."""
    super(ZeroMQBufferedQueue, self)._CreateZMQSocket()
    if not self._zmq_thread:
      thread_name = '{0:s}_zmq_responder'.format(self.name)
      self._zmq_thread = threading.Thread(
          target=self._ZeroMQResponder, args=[self._queue], name=thread_name)
      self._zmq_thread.start()

  @abc.abstractmethod
  def _ZeroMQResponder(self, source_queue):
    """Listens for requests and replies to clients.

    Args:
      source_queue (queue.queue): queue to to pull items from.
    """

  def Close(self, abort=False):
    """Closes the queue.

    Args:
      abort (Optional[bool]): whether the Close is the result of an abort
          condition. If True, queue contents may be lost.

    Raises:
      QueueAlreadyClosed: if the queue is not started, or has already been
          closed.
      RuntimeError: if closed or terminate event is missing.
    """
    if not self._closed_event or not self._terminate_event:
      raise RuntimeError('Missing closed or terminate event.')

    if not abort and self._closed_event.is_set():
      raise errors.QueueAlreadyClosed()

    self._closed_event.set()

    if abort:
      if not self._closed_event.is_set():
        logger.warning(
            '{0:s} queue aborting. Contents may be lost.'.format(self.name))

      # We can't determine whether a there might be an operation being performed
      # on the socket in a separate method or thread, so we'll signal that any
      # such operation should cease.
      self._terminate_event.set()

      self._linger_seconds = 0

      if self._zmq_thread:
        logger.debug('[{0:s}] Waiting for thread to exit.'.format(self.name))
        self._zmq_thread.join(timeout=self.timeout_seconds)
        if self._zmq_thread.is_alive():
          logger.error((
              '{0:s} ZMQ responder thread did not exit within timeout').format(
                  self.name))
    else:
      logger.debug(
          '{0:s} queue closing, will linger for up to {1:d} seconds'.format(
              self.name, self._linger_seconds))

  def Empty(self):
    """Removes all items from the internal buffer."""
    try:
      while True:
        self._queue.get(False)
    except queue.Empty:
      pass


class ZeroMQBufferedReplyQueue(ZeroMQBufferedQueue):
  """Parent class for buffered Plaso queues backed by ZeroMQ REP sockets.

  This class should not be instantiated directly, a subclass should be
  instantiated instead.

  Instances of this class or subclasses may only be used to push items, not to
  pop.
  """

  _ZMQ_SOCKET_RECEIVE_TIMEOUT_MILLISECONDS = 4000
  _ZMQ_SOCKET_SEND_TIMEOUT_MILLISECONDS = 2000

  _SOCKET_TYPE = zmq.REP

  def _ZeroMQResponder(self, source_queue):
    """Listens for requests and replies to clients.

    Args:
      source_queue (queue.Queue): queue to use to pull items from.

    Raises:
      RuntimeError: if closed or terminate event is missing.
    """
    if not self._closed_event or not self._terminate_event:
      raise RuntimeError('Missing closed or terminate event.')

    logger.debug('{0:s} responder thread started'.format(self.name))

    item = None
    while not self._terminate_event.is_set():
      if not item:
        try:
          if self._closed_event.is_set():
            item = source_queue.get_nowait()
          else:
            item = source_queue.get(True, self._buffer_timeout_seconds)

        except queue.Empty:
          if self._closed_event.is_set():
            break

          continue

      try:
        # We need to receive a request before we can reply with the item.
        self._ReceiveItemOnActivity(self._zmq_socket)

      except errors.QueueEmpty:
        if self._closed_event.is_set() and self._queue.empty():
          break

        continue

      sent_successfully = self._SendItem(self._zmq_socket, item)
      item = None
      if not sent_successfully:
        logger.error('Queue {0:s} unable to send item.'.format(self.name))
        break

    logger.info('Queue {0:s} responder exiting.'.format(self.name))
    self._zmq_socket.close(self._linger_seconds)

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
          or non-blocking mode.

    Raises:
      QueueAlreadyClosed: if the queue is closed.
      QueueFull: if the internal buffer was full and it was not possible to
          push the item to the buffer within the timeout.
      RuntimeError: if closed event is missing.
    """
    if not self._closed_event:
      raise RuntimeError('Missing closed event.')

    if self._closed_event.is_set():
      raise errors.QueueAlreadyClosed()

    if not self._zmq_socket:
      self._CreateZMQSocket()

    try:
      if block:
        self._queue.put(item, timeout=self.timeout_seconds)
      else:
        self._queue.put(item, block=False)
    except queue.Full as exception:
      raise errors.QueueFull(exception)


class ZeroMQBufferedReplyBindQueue(ZeroMQBufferedReplyQueue):
  """A Plaso queue backed by a ZeroMQ REP socket that binds to a port.

  This queue may only be used to pop items, not to push.
  """
  SOCKET_CONNECTION_TYPE = ZeroMQQueue.SOCKET_CONNECTION_BIND
