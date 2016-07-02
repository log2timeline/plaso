# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import abc
import logging
import multiprocessing
import os
import Queue
import random
import signal
import time

from plaso.engine import plaso_queue
from plaso.lib import errors
from plaso.multi_processing import xmlrpc


class MultiProcessBaseProcess(multiprocessing.Process):
  """Class that defines the multi-processing process interface.

  Attributes:
    rpc_port (int): port number of the process status RPC server.
  """

  _NUMBER_OF_RPC_SERVER_START_ATTEMPTS = 14
  _PROCESS_JOIN_TIMEOUT = 5.0

  def __init__(self, enable_sigsegv_handler=False, **kwargs):
    """Initializes the process object.

    Args:
      enable_sigsegv_handler (bool): True if the SIGSEGV handler should
                                     be enabled.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessBaseProcess, self).__init__(**kwargs)
    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._original_sigsegv_handler = None
    # TODO: check if this can be replaced by self.pid or does this only apply
    # to the parent process?
    self._pid = None
    self._rpc_server = None
    self._status_is_running = False

    # We need to share the RPC port number with the engine process.
    self.rpc_port = multiprocessing.Value(u'I', 0)

  @abc.abstractmethod
  def _GetStatus(self):
    """Returns a status dictionary."""

  @abc.abstractmethod
  def _Main(self):
    """The process main loop.

    This method is called when the process is ready to start. A sub class
    should override this method to do the necessary actions in the main loop.
    """

  def _OnCriticalError(self):
    """The process on critical error handler.

    This method is called when the process encountered a critical error e.g.
    a segfault. A sub class should override this method to do the necessary
    actions before the original critical error signal handler it called.

    Be aware that the state of the process should not be trusted a significant
    part of memory could have been overwritten before a segfault. This callback
    is primarily intended to salvage what we need to troubleshoot the error.
    """
    return

  def _SigSegvHandler(self, unused_signal_number, unused_stack_frame):
    """Signal handler for the SIGSEGV signal.

    Args:
      signal_number: Numeric representation of the signal.
      stack_frame: The current stack frame (instance of frame object) or None.
    """
    self._OnCriticalError()

    # Note that the original SIGSEGV handler can be 0.
    if self._original_sigsegv_handler is not None:
      # Let the original SIGSEGV handler take over.
      signal.signal(signal.SIGSEGV, self._original_sigsegv_handler)
      os.kill(self._pid, signal.SIGSEGV)

  def _SigTermHandler(self, unused_signal_number, unused_stack_frame):
    """Signal handler for the SIGTERM signal.

    Args:
      signal_number: Numeric representation of the signal.
      stack_frame: The current stack frame (instance of frame object) or None.
    """
    self.SignalAbort()

  def _StartProcessStatusRPCServer(self):
    """Starts the process status RPC server."""
    if self._rpc_server:
      return

    self._rpc_server = xmlrpc.XMLProcessStatusRPCServer(self._GetStatus)

    hostname = u'localhost'

    # Try the PID as port number first otherwise pick something random
    # between 1024 and 60000.
    if self._pid < 1024 or self._pid > 60000:
      port = random.randint(1024, 60000)
    else:
      port = self._pid

    if not self._rpc_server.Start(hostname, port):
      port = 0
      for _ in range(self._NUMBER_OF_RPC_SERVER_START_ATTEMPTS):
        port = random.randint(1024, 60000)
        if self._rpc_server.Start(hostname, port):
          break

        port = 0

    if not port:
      logging.error((
          u'Unable to start a process status RPC server for {0!s} '
          u'(PID: {1:d})').format(self._name, self._pid))
      self._rpc_server = None
      return

    self.rpc_port.value = port

    logging.debug(
        u'Process: {0!s} process status RPC server started'.format(self._name))

  def _StopProcessStatusRPCServer(self):
    """Stops the process status RPC server."""
    if not self._rpc_server:
      return

    # Make sure the engine gets one more status update so it knows
    # the worker has completed.
    self._WaitForStatusNotRunning()

    self._rpc_server.Stop()
    self._rpc_server = None
    self.rpc_port.value = 0

    logging.debug(
        u'Process: {0!s} process status RPC server stopped'.format(self._name))

  def _WaitForStatusNotRunning(self):
    """Waits for the status is running to change to false."""
    # We wait slightly longer than the status check sleep time.
    time.sleep(2.0)
    time_slept = 2.0
    while self._status_is_running:
      time.sleep(0.5)
      time_slept += 0.5
      if time_slept >= self._PROCESS_JOIN_TIMEOUT:
        break

  @property
  def name(self):
    """The process name."""
    return self._name

  # This method is part of the multiprocessing.Process interface hence
  # its name does not follow the style guide.
  def run(self):
    """Runs the process."""
    # Prevent KeyboardInterrupt being raised inside the process.
    # This will prevent a process generating a traceback when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # A SIGTERM signal handler is necessary to make sure IPC is cleaned up
    # correctly on terminate.
    signal.signal(signal.SIGTERM, self._SigTermHandler)

    # A SIGSEGV signal handler is necessary to try to indicate where
    # worker failed.
    # WARNING the SIGSEGV handler will deadlock the process on a real segfault.
    if self._enable_sigsegv_handler:
      self._original_sigsegv_handler = signal.signal(
          signal.SIGSEGV, self._SigSegvHandler)

    self._pid = os.getpid()

    # We need to set the is running status explicitly to True in case
    # the process completes before the engine is able to determine
    # the status of the process, e.g. in the unit tests.
    self._status_is_running = True

    logging.debug(
        u'Process: {0!s} (PID: {1:d}) started'.format(self._name, self._pid))

    self._StartProcessStatusRPCServer()

    self._Main()

    self._StopProcessStatusRPCServer()

    logging.debug(
        u'Process: {0!s} (PID: {1:d}) stopped'.format(self._name, self._pid))

    self._status_is_running = False

  @abc.abstractmethod
  def SignalAbort(self):
    """Signals the process to abort."""


class MultiProcessingQueue(plaso_queue.Queue):
  """Class that defines the multi-processing queue."""

  def __init__(self, maximum_number_of_queued_items=0, timeout=None):
    """Initializes the multi-processing queue object.

    Args:
      maximum_number_of_queued_items: The maximum number of queued items.
                                      The default is 0, which represents
                                      no limit.
      timeout: Optional floating point number of seconds for the get to
               time out. The default is None, which means the get will
               block until a new item is put onto the queue.
    """
    super(MultiProcessingQueue, self).__init__()
    self._timeout = timeout

    # maxsize contains the maximum number of items allowed to be queued,
    # where 0 represents unlimited.

    # We need to check that we aren't asking for a bigger queue than the
    # platform supports, which requires access to this protected member.
    # pylint: disable=protected-access
    queue_max_length = multiprocessing._multiprocessing.SemLock.SEM_VALUE_MAX
    # pylint: enable=protected-access

    if maximum_number_of_queued_items > queue_max_length:
      logging.warning((
          u'Requested maximum queue size: {0:d} is larger than the maximum '
          u'size supported by the system. Defaulting to: {1:d}').format(
              maximum_number_of_queued_items, queue_max_length))
      maximum_number_of_queued_items = queue_max_length

    # This queue appears not to be FIFO.
    self._queue = multiprocessing.Queue(maxsize=maximum_number_of_queued_items)

  def Open(self):
    """Opens the queue."""
    pass

  # pylint: disable=arguments-differ
  def Close(self, abort=False):
    """Closes the queue.

    This needs to be called from any process or thread putting items onto
    the queue.

    Args:
      abort: optional boolean to indicate the close is issued on abort.
    """
    if abort:
      # Prevent join_thread() from blocking.
      self._queue.cancel_join_thread()

    self._queue.close()
    self._queue.join_thread()

  def Empty(self):
    """Empties the queue."""
    try:
      while True:
        self._queue.get(False)
    except Queue.Empty:
      pass

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return self._queue.empty()

  def PushItem(self, item, block=True):
    """Pushes an item onto the queue.

    Args:
      block: boolean value to indicate put should block
             if the queue is full.
    """
    try:
      self._queue.put(item, block=block)

    # Queue.Full can be raised if block is False.
    # Since this should only be used in the abort code path
    # the exception is ignored.
    except Queue.Full:
      pass

  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      QueueClose: if the queue has already been closed.
      QueueEmpty: if no item could be retrieved from the queue within the
                  specified timeout.
    """
    try:
      # If no timeout is specified the queue will block if empty otherwise
      # a Queue.Empty exception is raised.
      return self._queue.get(timeout=self._timeout)
    except KeyboardInterrupt:
      raise errors.QueueClose
    # If close() is called on the multiprocessing.Queue while it is blocking
    # on get() it will raise IOError.
    except IOError:
      raise errors.QueueClose
    except Queue.Empty:
      raise errors.QueueEmpty
