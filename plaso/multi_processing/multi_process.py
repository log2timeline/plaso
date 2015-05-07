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
  if sys.platform.startswith('win'):
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

  _PROCESS_ABORT_TIMEOUT = 2
  _PROCESS_JOIN_TIMEOUT = 5
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
    collection_queue = MultiProcessingQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)
    storage_queue = MultiProcessingQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)
    parse_error_queue = MultiProcessingQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)

    super(MultiProcessEngine, self).__init__(
        collection_queue, storage_queue, parse_error_queue)

    self._collection_process = None
    self._foreman_object = None
    self._storage_writer_completed = False
    self._storage_writer_process = None

    # TODO: turn into a process pool.
    self._worker_processes = []

  def _AbortKill(self):
    """Abort processing by sending SIGKILL or equivalent."""
    if self._collection_process and self._collection_process.is_alive():
      logging.warning(u'Killing collection process: {0:d}.'.format(
          self._collection_process.pid))
      SigKill(self._collection_process.pid)

    for worker_process in self._worker_processes:
      if worker_process.is_alive():
        logging.warning(u'Killing worker: {0:s} process: {1:d}'.format(
            worker_process.name, worker_process.pid))
        SigKill(worker_process.pid)

    if self._storage_writer_process and self._storage_writer_process.is_alive():
      logging.warning(u'Killing storage process: {0:d}.'.format(
          self._storage_writer_process.pid))
      SigKill(self._storage_writer_process.pid)

  def _AbortNormal(self, timeout=None):
    """Abort in a normal way.

    Args:
      timeout: The process join timeout. The default is None meaning
               no timeout.
    """
    if self._collection_process:
      logging.warning(u'Signaling collection process to abort.')
      self._collection_process.SignalAbort()

    if self._worker_processes:
      logging.warning(u'Signaling worker processes to abort.')
      for worker_process in self._worker_processes:
        worker_process.SignalAbort()

    logging.warning(u'Signaling storage process to abort.')
    self._event_queue_producer.SignalAbort()
    self._storage_writer_process.SignalAbort()

    if self._collection_process:
      logging.warning(u'Waiting for collection process (PID: {0:d}).'.format(
          self._collection_process.pid))
      # TODO: it looks like xmlrpclib.ServerProxy is not allowing the
      # collection process to close.
      self._collection_process.join(timeout=timeout)
      if self._collection_process.is_alive():
        logging.warning(
            u'Waiting for collection process (PID: {0:d}) failed'.format(
                self._collection_process.pid))

    for worker_process in self._worker_processes:
      logging.warning(
          u'Waiting for worker: {0:s} process (PID: {1:d})'.format(
              worker_process.name, worker_process.pid))
      worker_process.join(timeout=timeout)
      if worker_process.is_alive():
        logging.warning(
            u'Waiting for worker: {0:s} process (PID: {1:d}) failed'.format(
                worker_process.name, worker_process.pid))

    if self._storage_writer_process:
      logging.warning(u'Waiting for storage process (PID: {0:d}).'.format(
          self._collection_process.pid))
      self._storage_writer_process.join(timeout=timeout)
      if self._storage_writer_process.is_alive():
        logging.warning(
            u'Waiting for storage process (PID: {0:d}) failed'.format(
                self._storage_writer_process.pid))

  def _AbortTerminate(self):
    """Abort processing by sending SIGTERM or equivalent."""
    if self._collection_process and self._collection_process.is_alive():
      logging.warning(u'Terminating collection process: {0:d}.'.format(
          self._collection_process.pid))
      self._collection_process.terminate()

    for worker_process in self._worker_processes:
      if worker_process.is_alive():
        logging.warning(u'Terminating worker: {0:s} process: {1:d}'.format(
            worker_process.name, worker_process.pid))
        worker_process.terminate()

    if self._storage_writer_process and self._storage_writer_process.is_alive():
      logging.warning(u'Terminating storage process: {0:d}.'.format(
          self._storage_writer_process.pid))
      self._storage_writer_process.terminate()

  def CreateCollector(
      self, include_directory_stat, vss_stores=None, filter_find_specs=None,
      resolver_context=None):
    """Creates a collector object.

    The collector discovers all the files that need to be processed by
    the workers. Once a file is discovered it is added to the process queue
    as a path specification (instance of dfvfs.PathSpec).

    Args:
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected.
      vss_stores: Optional list of VSS stores to include in the collection,
                  where 1 represents the first store. Set to None if no
                  VSS stores should be processed. The default is None.
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      A collector object (instance of Collector).

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_path_spec:
      raise RuntimeError(u'Missing source.')

    collector_object = collector.Collector(
        self._collection_queue, self._source, self._source_path_spec,
        resolver_context=resolver_context)

    collector_object.SetCollectDirectoryMetadata(include_directory_stat)

    if vss_stores:
      collector_object.SetVssInformation(vss_stores)

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
        worker_number, self._collection_queue, self._event_queue_producer,
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

  def ProcessSource(
      self, collector_object, storage_writer, hasher_names_string=None,
      number_of_extraction_workers=0, parser_filter_string=None,
      status_update_callback=None, show_memory_usage=False):
    """Processes the source and extracts event objects.

    Args:
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

    self._foreman_object = foreman.Foreman(
        self._event_queue_producer, show_memory_usage=show_memory_usage)

    logging.info(u'Starting processes.')
    self._storage_writer_process = MultiProcessStorageWriterProcess(
        storage_writer, name=u'StorageWriter')
    self._storage_writer_process.start()
    self._foreman_object.StartProcessMonitoring(self._storage_writer_process)

    for worker_number in range(number_of_extraction_workers):
      extraction_worker = self.CreateExtractionWorker(worker_number)

      process_name = u'Worker_{0:d}'.format(worker_number)

      # TODO: Test to see if a process pool can be a better choice.
      worker_process = MultiProcessEventExtractionWorkerProcess(
          extraction_worker, parser_filter_string, hasher_names_string,
          name=process_name)
      worker_process.start()

      self._foreman_object.StartProcessMonitoring(worker_process)
      self._worker_processes.append(worker_process)

    self._collection_process = MultiProcessCollectionProcess(
        collector_object, name=u'Collector')
    self._collection_process.start()
    self._foreman_object.StartProcessMonitoring(self._collection_process)

    logging.debug(u'Processing started.')

    time.sleep(self._FOREMAN_CHECK_SLEEP)
    while not self._foreman_object.CheckStatus():
      if status_update_callback:
        status_update_callback(self._foreman_object.processing_status)

      time.sleep(self._FOREMAN_CHECK_SLEEP)

    logging.info(u'Processing stopped.')

    # TODO: remove the processes from the foreman.

    self._StopProcesses(collector_object)

  def _StopProcesses(self, collector_object):
    """Stops the processes.

    Args:
      collector_object: A collector object (instance of Collector).
    """
    logging.info(u'Waiting for collector process.')
    self._collection_process.join(timeout=self._PROCESS_JOIN_TIMEOUT)
    if self._collection_process.is_alive():
      logging.warning((
          u'Forcing termination of collector process (PID: {0:d})').format(
              self._collection_process.pid))

      self._collection_process.terminate()

    logging.info(u'Collector process stopped.')

    # Remove the extraction worker processes from the foreman and wake them
    # to make usre that they are not blocking waiting for new items.
    for worker_process in self._worker_processes:
      self._foreman_object.StopProcessMonitoring(worker_process.pid)
      collector_object.SignalAbort()

    # Join or terminate the extraction worker processes.
    for worker_process in self._worker_processes:
      logging.info((
          u'Waiting for extraction worker process: {0!s} '
          u'(PID: {1:d}).').format(worker_process.name, worker_process.pid))
      worker_process.join(timeout=self._PROCESS_JOIN_TIMEOUT)
      if worker_process.is_alive():
        logging.warning((
            u'Forcing termination of extraction worker process: {0!s} '
            u'(PID: {1:d})').format(worker_process.name, worker_process.pid))

        worker_process.terminate()

      logging.info(
          u'Extraction worker process: {0!s} stopped.'.format(
              worker_process.name))

    # Remove the storage writer process from the foreman and wake it
    # to make sure it is not blocking waiting for new items.
    self._foreman_object.StopProcessMonitoring(self._storage_writer_process.pid)
    self._event_queue_producer.SignalAbort()
    self._parse_error_queue_producer.SignalAbort()

    logging.info(u'Waiting for storage writer process.')
    self._storage_writer_process.join(timeout=self._PROCESS_JOIN_TIMEOUT)
    if self._storage_writer_process.is_alive():
      logging.warning((
          u'Forcing termination of storage writer process (PID: {0:d})').format(
              self._storage_writer_process.pid))

      self._storage_writer_process.terminate()

    logging.info(u'Storage writer process stopped.')

    self._foreman_object = None

  def SignalAbort(self):
    """Signals the engine to abort."""
    super(MultiProcessEngine, self).SignalAbort()

    try:
      self._AbortNormal(timeout=self._PROCESS_ABORT_TIMEOUT)
      self._AbortTerminate()
    except KeyboardInterrupt:
      self._AbortKill()

    # TODO: remove the need for this.
    # Sometimes the main process will be unresponsive.
    SigKill(os.getpid())


class MultiProcessBaseProcess(multiprocessing.Process):
  """Class that defines the multi-processing process interface."""

  def __init__(self, **kwargs):
    """Initializes the process object.

    Args:
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessBaseProcess, self).__init__(**kwargs)
    # TODO: check if this can be replaced by self.pid or does this only apply
    # to the parent process?
    self._pid = None
    self._rpc_server = None
    self._status_is_running = False

  @abc.abstractmethod
  def _GetStatus(self):
    """Returns a status dictionary."""

  @abc.abstractmethod
  def _Main(self):
    """The process main loop."""

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
    # the worker has completed. Hence we wait slightly longer than
    # the foreman sleep time.
    time.sleep(2.0)
    time_slept = 2.0
    while self._status_is_running:
      time.sleep(0.5)
      time_slept += 0.5
      if time_slept >= 5.0:
        break

    self._rpc_server.Stop()
    self._rpc_server = None

    logging.debug(
        u'Process: {0!s} process status RPC server stopped'.format(self._name))

  @property
  def name(self):
    """The process name."""
    return self._name

  # This method part of the multiprocessing.Process interface hence its name
  # is not following the style guide.
  def run(self):
    """Runs the process."""
    # Prevent the KeyboardInterrupt being raised inside the process.
    # This will prevent a process to generate a traceback when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    self._pid = os.getpid()

    # We need to set the is running statue explictily to True in case
    # the process completes before the foreman is able to determine
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


class MultiProcessCollectionProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing collection process."""

  def __init__(self, collector_object, **kwargs):
    """Initializes the process object.

    Args:
      collector_object: A collector object (instance of Collector).
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessCollectionProcess, self).__init__(**kwargs)
    self._collector = collector_object

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._collector.GetStatus()
    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    logging.info(u'Collector (PID: {0:d}) started'.format(self._pid))
    self._collector.Collect()
    logging.info(u'Collector (PID: {0:d}) stopped'.format(self._pid))

  def SignalAbort(self):
    """Signals the process to abort."""
    self._collector.SignalAbort()


class MultiProcessEventExtractionWorkerProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing event extraction worker process."""

  def __init__(self, extraction_worker, parser_filter_string,
               hasher_names_string, **kwargs):
    """Initializes the process object.

    Args:
      extraction_worker: The extraction worker object (instance of
                         MultiProcessEventExtractionWorker).
      parser_filter_string: The parser filter string.
      hasher_names_string: Optional comma separated string of names of
                           hashers to enable enable. The default is None.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(MultiProcessEventExtractionWorkerProcess, self).__init__(**kwargs)
    self._extraction_worker = extraction_worker

    # TODO: clean this up with the implementation of a task based
    # multi-processing approach.
    self._parser_filter_string = parser_filter_string
    self._hasher_names_string = hasher_names_string

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._extraction_worker.GetStatus()
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

  def SignalAbort(self):
    """Signals the process to abort."""
    self._extraction_worker.SignalAbort()


class MultiProcessStorageWriterProcess(MultiProcessBaseProcess):
  """Class that defines a multi-processing storage writer process."""

  def __init__(self, storage_writer, **kwargs):
    """Initializes the process object.

    Args:
      storage_writer: A storage writer object (instance of BaseStorageWriter).
    """
    super(MultiProcessStorageWriterProcess, self).__init__(**kwargs)
    self._storage_writer = storage_writer

  def _GetStatus(self):
    """Returns a status dictionary."""
    status = self._storage_writer.GetStatus()
    self._status_is_running = status.get(u'is_running', False)
    return status

  def _Main(self):
    """The main loop."""
    logging.info(u'Storage writer (PID: {0:d}) started.'.format(self._pid))
    self._storage_writer.WriteEventObjects()
    logging.info(u'Storage writer (PID: {0:d}) stopped.'.format(self._pid))

  def SignalAbort(self):
    """Signals the process to abort."""
    return


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
      logging.warn(
          u'Maximum queue size requested ({0:d}) is larger than system '
          u'supported maximum size. Setting queue size to maximum supported '
          u'size, '
          u'({1:d})'.format(maximum_number_of_queued_items, queue_max_length))
      maximum_number_of_queued_items = queue_max_length

    # This queue appears not to be FIFO.
    self._queue = multiprocessing.Queue(maxsize=maximum_number_of_queued_items)

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return self._queue.empty()

  def PushItem(self, item):
    """Pushes an item onto the queue."""
    self._queue.put(item)

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
    except Queue.Empty:
      raise errors.QueueEmpty
