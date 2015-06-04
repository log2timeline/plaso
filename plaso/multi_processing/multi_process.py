# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import abc
import ctypes
import logging
import multiprocessing
import os
import Queue
import signal
import sys
import time

from dfvfs.resolver import context

from plaso.engine import collector
from plaso.engine import engine
from plaso.engine import queue
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import foreman
from plaso.multi_processing import rpc
from plaso.multi_processing import xmlrpc
from plaso.parsers import mediator as parsers_mediator


def SigKill(pid):
  """Convenience function to issue a SIGKILL or equivalent.

  Args:
    pid: The process identifier.
  """
  if sys.platform.startswith(u'win'):
    process_terminate = 1
    handle = ctypes.windll.kernel32.OpenProcess(
        process_terminate, False, pid)
    ctypes.windll.kernel32.TerminateProcess(handle, -1)
    ctypes.windll.kernel32.CloseHandle(handle)

  else:
    try:
      os.kill(pid, signal.SIGKILL)
    except OSError as exception:
      logging.error(
          u'Unable to kill process {0:d} with error: {1:s}'.format(
              pid, exception))


class MultiProcessEngine(engine.BaseEngine):
  """Class that defines the multi-process engine."""

  _FOREMAN_CHECK_SLEEP = 1.5

  _PROCESS_ABORT_TIMEOUT = 2.0
  _PROCESS_JOIN_TIMEOUT = 5.0
  _PROCESS_TERMINATION_SLEEP = 0.5

  _WORKER_PROCESSES_MINIMUM = 2
  _WORKER_PROCESSES_MAXIMUM = 15

  def __init__(self, maximum_number_of_queued_items=0):
    """Initialize the multi-process engine object.

    Args:
      maximum_number_of_queued_items: The maximum number of queued items.
                                      The default is 0, which represents
                                      no limit.
    """
    path_spec_queue = MultiProcessingQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)
    event_object_queue = MultiProcessingQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)
    parse_error_queue = MultiProcessingQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)

    super(MultiProcessEngine, self).__init__(
        path_spec_queue, event_object_queue, parse_error_queue)

    self._number_of_extraction_workers = 0
    self._foreman_object = None
    self._stop_process_event = None
    self._storage_writer_completed = False

  def CreateCollector(
      self, include_directory_stat, filter_find_specs=None,
      resolver_context=None):
    """Creates a collector object.

    The collector discovers all the files that need to be processed by
    the workers. Once a file is discovered it is added to the process queue
    as a path specification (instance of dfvfs.PathSpec).

    Args:
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected.
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      A collector object (instance of Collector).
    """
    collector_object = collector.Collector(
        self._path_spec_queue, resolver_context=resolver_context)

    collector_object.SetCollectDirectoryMetadata(include_directory_stat)

    if filter_find_specs:
      collector_object.SetFilter(filter_find_specs)

    return collector_object

  def CreateExtractionWorker(self, worker_number):
    """Creates an extraction worker object.

    Args:
      worker_number: A number that identifies the worker.

    Returns:
      An extraction worker (instance of worker.ExtractionWorker).
    """
    parser_mediator = parsers_mediator.ParserMediator(
        self._event_queue_producer, self._parse_error_queue_producer,
        self.knowledge_base)

    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    resolver_context = context.Context()

    extraction_worker = worker.BaseEventExtractionWorker(
        worker_number, self._path_spec_queue, self._event_queue_producer,
        self._parse_error_queue_producer, parser_mediator,
        resolver_context=resolver_context)

    extraction_worker.SetEnableDebugOutput(self._enable_debug_output)

    extraction_worker.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type)

    if self._process_archive_files:
      extraction_worker.SetProcessArchiveFiles(self._process_archive_files)

    if self._filter_object:
      extraction_worker.SetFilterObject(self._filter_object)

    if self._mount_path:
      extraction_worker.SetMountPath(self._mount_path)

    if self._text_prepend:
      extraction_worker.SetTextPrepend(self._text_prepend)

    return extraction_worker

  def ProcessSources(
      self, source_path_specs, collector_object, storage_writer,
      hasher_names_string=None, number_of_extraction_workers=0,
      parser_filter_string=None, status_update_callback=None,
      show_memory_usage=False):
    """Processes the sources and extract event objects.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      collector_object: A collector object (instance of Collector).
      storage_writer: A storage writer object (instance of BaseStorageWriter).
      hasher_names_string: Optional comma separated string of names of
                           hashers to enable enable. The default is None.
      number_of_extraction_workers: Optional number of extraction worker
                                    processes. The default is 0 which means
                                    the function will determine the suitable
                                    number.
      parser_filter_string: Optional parser filter string. The default is None.
      status_update_callback: Optional callback function for status updates.
                              The default is None.
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging. The default is False.

    Returns:
      A boolean value indicating the sources were processed without
      unrecoverable errors or being aborted.
    """
    if number_of_extraction_workers < 1:
      # One worker for each "available" CPU (minus other processes).
      # The number here is derived from the fact that the engine starts up:
      # * A collection process.
      # * A storage process.
      #
      # If we want to utilize all CPUs on the system we therefore need to start
      # up workers that amounts to the total number of CPUs - the other
      # processes.
      cpu_count = multiprocessing.cpu_count() - 2

      if cpu_count <= self._WORKER_PROCESSES_MINIMUM:
        cpu_count = self._WORKER_PROCESSES_MINIMUM

      elif cpu_count >= self._WORKER_PROCESSES_MAXIMUM:
        cpu_count = self._WORKER_PROCESSES_MAXIMUM

      number_of_extraction_workers = cpu_count

    self._number_of_extraction_workers = number_of_extraction_workers
    self._foreman_object = foreman.Foreman(
        self._path_spec_queue, self.event_object_queue,
        self._parse_error_queue, show_memory_usage=show_memory_usage)

    logging.info(u'Starting processes.')
    self._stop_process_event = multiprocessing.Event()

    storage_writer_process = MultiProcessStorageWriterProcess(
        self._stop_process_event, self.event_object_queue,
        self._parse_error_queue, storage_writer, name=u'StorageWriter')
    storage_writer_process.start()
    self._foreman_object.RegisterProcess(storage_writer_process)

    for worker_number in range(self._number_of_extraction_workers):
      extraction_worker = self.CreateExtractionWorker(worker_number)

      process_name = u'Worker_{0:02d}'.format(worker_number)

      # TODO: Test to see if a process pool can be a better choice.
      worker_process = MultiProcessEventExtractionWorkerProcess(
          self._stop_process_event, self._path_spec_queue,
          self.event_object_queue, self._parse_error_queue,
          extraction_worker, parser_filter_string, hasher_names_string,
          name=process_name)
      worker_process.start()

      self._foreman_object.RegisterProcess(worker_process)

    collection_process = MultiProcessCollectionProcess(
        self._stop_process_event, source_path_specs, self._path_spec_queue,
        collector_object, name=u'Collector')
    collection_process.start()
    self._foreman_object.RegisterProcess(collection_process)

    self._foreman_object.StartProcessMonitoring()

    try:
      logging.debug(u'Processing started.')

      time.sleep(self._FOREMAN_CHECK_SLEEP)
      while not self._foreman_object.CheckStatus():
        if status_update_callback:
          status_update_callback(self._foreman_object.processing_status)

        time.sleep(self._FOREMAN_CHECK_SLEEP)

      logging.debug(u'Processing stopped.')
    except errors.ForemanAbort as exception:
      logging.warning(
          u'Processing aborted with error: {0:s}.'.format(exception))

    except Exception as exception:
      logging.error(
          u'Processing aborted with error: {0:s}.'.format(exception))
      self._foreman_object.error_detected = True

    self._StopExtractionProcesses(abort=self._foreman_object.error_detected)

    # TODO: kept here for testing now but this should be moved to
    # an error report that is provided after processing.
    # for path_spec_comparable in self._foreman_object._error_path_specs:
    #   logging.error(path_spec_comparable)

    return self._foreman_object.error_detected

  def _StopExtractionProcesses(self, abort=False):
    """Stops the extraction processes.

    Args:
      abort: optional boolean to indicate the stop is issued on abort.
    """
    self._foreman_object.StopProcessMonitoring()

    self._stop_process_event.set()

    if abort:
      super(MultiProcessEngine, self).SignalAbort()

      # Signal all the processes to abort.
      self._foreman_object.AbortTerminate()

    # Note that multiprocessing.Queue is very sensitive regarding
    # blocking on either a get or a put. So we try to prevent using
    # any blocking behavior.

    # Wake the processes to make sure that they are not blocking
    # waiting for new items.
    for _ in range(self._number_of_extraction_workers):
      self._path_spec_queue.PushItem(queue.QueueAbort(), block=False)

    self.event_object_queue.PushItem(queue.QueueAbort(), block=False)
    # TODO: enable this when the parse error queue consumer is operational.
    # self._parse_error_queue.PushItem(queue.QueueAbort(), block=False)

    # Try terminating the processes in the normal way.
    self._foreman_object.AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

    if not abort:
      # Check if the processes are still alive and terminate them if necessary.
      self._foreman_object.AbortTerminate()
      self._foreman_object.AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

    # Set abort to True to stop queue.join_thread() from blocking.
    self._path_spec_queue.Close(abort=True)
    self.event_object_queue.Close(abort=True)
    self._parse_error_queue.Close(abort=True)

  def SignalAbort(self):
    """Signals the engine to abort."""
    try:
      self._StopExtractionProcesses(abort=True)

      # Kill any remaining processes.
      self._foreman_object.AbortKill()

    except KeyboardInterrupt:
      self._foreman_object.AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrecly finalized IPC.
      SigKill(os.getpid())


class MultiProcessBaseProcess(multiprocessing.Process):
  """Class that defines the multi-processing process interface."""

  _PROCESS_JOIN_TIMEOUT = 5.0

  def __init__(self, process_type, stop_process_event, **kwargs):
    """Initializes the process object.

    Args:
      process_type: the process type.
      stop_process_event: the stop process event (instance of
                          multiprocessing.Event). The process should exit
                          after this event is set.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessBaseProcess, self).__init__(**kwargs)
    self._original_sigsegv_handler = None
    # TODO: check if this can be replaced by self.pid or does this only apply
    # to the parent process?
    self._pid = None
    self._rpc_server = None
    self._status_is_running = False
    self._stop_process_event = stop_process_event
    self._type = process_type

  @abc.abstractmethod
  def _GetStatus(self):
    """Returns a status dictionary."""

  @abc.abstractmethod
  def _Main(self):
    """The process main loop.

    This method is called when the process is ready to start. A sub class
    should override this method to do the necessary actions in the main loop.
    """

  def _OnExit(self):
    """The process on exit handler.

    This method is called when the process is ready to exit. A sub class
    should override this method to do the necessary actions up after
    the main loop.
    """
    return

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
    port = rpc.GetProxyPortNumberFromPID(self._pid)

    if not self._rpc_server.Start(hostname, port):
      logging.error((
          u'Unable to start a process status RPC server for {0!s} '
          u'(PID: {1:d})').format(self._name, self._pid))

      self._rpc_server = None
      return

    logging.debug(
        u'Process: {0!s} process status RPC server started'.format(self._name))

  def _StopProcessStatusRPCServer(self):
    """Stops the process status RPC server."""
    if not self._rpc_server:
      return

    # Make sure the foreman gets one more status update so it knows
    # the worker has completed.
    self._WaitForStatusNotRunning()

    self._rpc_server.Stop()
    self._rpc_server = None

    logging.debug(
        u'Process: {0!s} process status RPC server stopped'.format(self._name))

  def _WaitForStatusNotRunning(self):
    """Waits for the status is running to change to false."""
    # We wait slightly longer than the foreman sleep time.
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

  @property
  def type(self):
    """The process type."""
    return self._type

  # This method is part of the multiprocessing.Process interface hence
  # its name does not follow the style guide.
  def run(self):
    """Runs the process."""
    # Prevent the KeyboardInterrupt being raised inside the process.
    # This will prevent a process to generate a traceback when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # A SIGTERM signal handler is necessary to make sure IPC is cleaned up
    # correctly on terminate.
    signal.signal(signal.SIGTERM, self._SigTermHandler)

    # A SIGSEGV signal handler is necessary to try to indicate where
    # worker failed.
    self._original_sigsegv_handler = signal.signal(
        signal.SIGSEGV, self._SigSegvHandler)

    self._pid = os.getpid()

    # We need to set the is running statue explictily to True in case
    # the process completes before the foreman is able to determine
    # the status of the process, e.g. in the unit tests.
    self._status_is_running = True

    logging.debug(
        u'Process: {0!s} (PID: {1:d}) started'.format(self._name, self._pid))

    self._StartProcessStatusRPCServer()

    self._Main()
    self._stop_process_event.wait()
    self._OnExit()

    self._StopProcessStatusRPCServer()

    logging.debug(
        u'Process: {0!s} (PID: {1:d}) stopped'.format(self._name, self._pid))

    self._status_is_running = False

  @abc.abstractmethod
  def SignalAbort(self):
    """Signals the process to abort."""


class MultiProcessCollectionProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing collection process."""

  def __init__(
      self, stop_process_event, source_path_specs, path_spec_queue,
      collector_object, **kwargs):
    """Initializes the process object.

    Args:
      stop_process_event: the stop process event (instance of
                          multiprocessing.Event). The process should exit
                          after this event is set.
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      path_spec_queue: the path specification queue object (instance of
                       MultiProcessingQueue).
      collector_object: A collector object (instance of Collector).
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessCollectionProcess, self).__init__(
        definitions.PROCESS_TYPE_COLLECTOR, stop_process_event, **kwargs)
    self._collector = collector_object
    self._path_spec_queue = path_spec_queue
    self._source_path_specs = source_path_specs

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._collector.GetStatus()
    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    logging.debug(u'Collector (PID: {0:d}) started'.format(self._pid))

    # The collector will typically collect the path specifications and
    # exit. However multiprocessing.Queue will start a separate thread
    # that blocks on close until every item is read from the queue. This
    # is necessary since the queue uses a pipe under the hood. However
    # this behavior causes unwanted side effect for the abort code paths
    # hence we have the process wait for the stop process event and then
    # close the queue with out the separate blocking thread.

    self._collector.Collect(self._source_path_specs)

    logging.debug(u'Collector (PID: {0:d}) stopped'.format(self._pid))

  def _OnExit(self):
    """The process on exit handler."""
    logging.debug(u'Collector (PID: {0:d}) on exit'.format(self._pid))

    self._path_spec_queue.Close(abort=True)

  def SignalAbort(self):
    """Signals the process to abort."""
    self._collector.SignalAbort()


class MultiProcessEventExtractionWorkerProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing event extraction worker process."""

  def __init__(
      self, stop_process_event, path_spec_queue, event_object_queue,
      parse_error_queue, extraction_worker, parser_filter_string,
      hasher_names_string, **kwargs):
    """Initializes the process object.

    Args:
      stop_process_event: the stop process event (instance of
                          multiprocessing.Event). The process should exit
                          after this event is set.
      path_spec_queue: the path specification queue object (instance of
                       MultiProcessingQueue).
      event_object_queue: the event object queue object (instance of
                          MultiProcessingQueue).
      parse_error_queue: the parser error queue object (instance of
                         MultiProcessingQueue).
      extraction_worker: The extraction worker object (instance of
                         MultiProcessEventExtractionWorker).
      parser_filter_string: The parser filter string.
      hasher_names_string: The hasher names string.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessEventExtractionWorkerProcess, self).__init__(
        definitions.PROCESS_TYPE_WORKER, stop_process_event, **kwargs)
    self._critical_error = False
    self._extraction_worker = extraction_worker
    self._event_object_queue = event_object_queue
    self._parse_error_queue = parse_error_queue
    self._path_spec_queue = path_spec_queue

    # TODO: clean this up with the implementation of a task based
    # multi-processing approach.
    self._parser_filter_string = parser_filter_string
    self._hasher_names_string = hasher_names_string

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._extraction_worker.GetStatus()
    if self._critical_error:
      # Note seem unable to pass objects here.
      current_path_spec = self._extraction_worker.current_path_spec
      status[u'path_spec'] = current_path_spec.comparable
      status[u'processing_status'] = definitions.PROCESSING_STATUS_ERROR

    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    # We need to initialize the parser and hasher objects after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    self._extraction_worker.InitializeParserObjects(
        parser_filter_string=self._parser_filter_string)

    if self._hasher_names_string:
      self._extraction_worker.SetHashers(self._hasher_names_string)

    logging.debug(u'Extraction worker: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    self._extraction_worker.Run()

    logging.debug(u'Extraction worker: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

  def _OnCriticalError(self):
    """The process on critical error handler."""
    self._critical_error = True
    self._WaitForStatusNotRunning()

  def _OnExit(self):
    """The process on exit handler."""
    logging.debug(u'Extraction worker: {0!s} (PID: {1:d}) on exit'.format(
        self._name, self._pid))

    self._path_spec_queue.Close(abort=True)
    self._event_object_queue.Close(abort=True)
    self._parse_error_queue.Close(abort=True)

  def SignalAbort(self):
    """Signals the process to abort."""
    self._extraction_worker.SignalAbort()


class MultiProcessStorageWriterProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing storage writer process."""

  def __init__(
      self, stop_process_event, event_object_queue, parse_error_queue,
      storage_writer, **kwargs):
    """Initializes the process object.

    Args:
      stop_process_event: the stop process event (instance of
                          multiprocessing.Event). The process should exit
                          after this event is set.
      event_object_queue: the event object queue object (instance of
                          MultiProcessingQueue).
      parse_error_queue: the parser error queue object (instance of Queue).
      storage_writer: A storage writer object (instance of BaseStorageWriter).
    """
    super(MultiProcessStorageWriterProcess, self).__init__(
        definitions.PROCESS_TYPE_STORAGE_WRITER, stop_process_event, **kwargs)
    self._event_object_queue = event_object_queue
    self._parse_error_queue = parse_error_queue
    self._storage_writer = storage_writer

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._storage_writer.GetStatus()
    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    logging.debug(u'Storage writer (PID: {0:d}) started.'.format(self._pid))

    self._storage_writer.WriteEventObjects()

    logging.debug(u'Storage writer (PID: {0:d}) stopped.'.format(self._pid))

  def _OnExit(self):
    """The process on exit handler."""
    logging.debug(u'Storage writer (PID: {0:d}) on exit.'.format(self._pid))

  def SignalAbort(self):
    """Signals the process to abort."""
    self._storage_writer.SignalAbort()


class MultiProcessingQueue(queue.Queue):
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
    """Pops an item off the queue or None on timeout.

    Raises:
      QueueEmpty: when the queue is empty.
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
