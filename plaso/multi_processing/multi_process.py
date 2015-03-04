# -*- coding: utf-8 -*-
"""The multi-process processing engine."""

import ctypes
import logging
import multiprocessing
import os
import signal
import sys
import threading

from dfvfs.resolver import context

from plaso.engine import collector
from plaso.engine import engine
from plaso.engine import queue
from plaso.engine import worker
from plaso.lib import errors
from plaso.multi_processing import foreman
from plaso.multi_processing import rpc_proxy
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
    self._storage_process = None

    # TODO: turn into a process pool.
    self._worker_processes = {}

    # Attributes for RPC proxy server thread.
    self._proxy_thread = None
    self._rpc_proxy_server = None
    self._rpc_port_number = 0

  def _StartRPCProxyServerThread(self, foreman_object):
    """Starts the RPC proxy server thread.

    Args:
      foreman_object: a foreman object (instance of Foreman).
    """
    if self._rpc_proxy_server or self._proxy_thread:
      return

    self._rpc_proxy_server = rpc_proxy.StandardRpcProxyServer(os.getpid())

    try:
      self._rpc_proxy_server.Open()
      self._rpc_proxy_server.RegisterFunction(
          'signal_end_of_collection', foreman_object.SignalEndOfProcessing)

      self._proxy_thread = threading.Thread(
          name='rpc_proxy', target=self._rpc_proxy_server.StartProxy)
      self._proxy_thread.start()

      self._rpc_port_number = self._rpc_proxy_server.listening_port

    except errors.ProxyFailedToStart as exception:
      logging.error((
          u'Unable to setup a RPC server for the engine with error '
          u'{0:s}').format(exception))

  def _StopRPCProxyServerThread(self):
    """Stops the RPC proxy server thread."""
    if not self._rpc_proxy_server or not self._proxy_thread:
      return

    # Close the proxy, free up resources so we can shut down the thread.
    self._rpc_proxy_server.Close()

    if self._proxy_thread.isAlive():
      self._proxy_thread.join()

    self._proxy_thread = None
    self._rpc_proxy_server = None
    self._rpc_port_number = 0

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

    # TODO: move profiler in separate object.
    extraction_worker.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate)

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
      self, collector_object, storage_writer, parser_filter_string=None,
      hasher_names_string=None, number_of_extraction_workers=0,
      have_collection_process=True, have_foreman_process=True,
      show_memory_usage=False):
    """Processes the source and extracts event objects.

    Args:
      collector_object: A collector object (instance of Collector).
      storage_writer: A storage writer object (instance of BaseStorageWriter).
      parser_filter_string: Optional parser filter string. The default is None.
      hasher_names_string: Optional comma separated string of names of
                           hashers to enable enable. The default is None.
      number_of_extraction_workers: Optional number of extraction worker
                                    processes. The default is 0 which means
                                    the function will determine the suitable
                                    number.
      have_collection_process: Optional boolean value to indicate a separate
                               collection process should be run. The default
                               is True.
      have_foreman_process: Optional boolean value to indicate a separate
                            foreman process should be run to make sure the
                            workers are extracting event objects. The default
                            is True.
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging. The default is False.
    """
    if number_of_extraction_workers < 1:
      # One worker for each "available" CPU (minus other processes).
      # The number here is derived from the fact that the engine starts up:
      #   + A collector process (optional).
      #   + A storage process.
      #
      # If we want to utilize all CPUs on the system we therefore need to start
      # up workers that amounts to the total number of CPUs - the other
      # processes.
      cpu_count = multiprocessing.cpu_count() - 2
      if have_collection_process:
        cpu_count -= 1

      if cpu_count <= self._WORKER_PROCESSES_MINIMUM:
        cpu_count = self._WORKER_PROCESSES_MINIMUM

      elif cpu_count >= self._WORKER_PROCESSES_MAXIMUM:
        cpu_count = self._WORKER_PROCESSES_MAXIMUM

      number_of_extraction_workers = cpu_count

    if have_foreman_process:
      self._foreman_object = foreman.Foreman(
          show_memory_usage=show_memory_usage)
      self._StartRPCProxyServerThread(self._foreman_object)

    self._storage_process = MultiProcessStorageProcess(
        storage_writer, name='StorageProcess')
    self._storage_process.start()

    if have_collection_process:
      self._collection_process = MultiProcessCollectionProcess(
          collector_object, self._rpc_port_number, name='CollectionProcess')
      self._collection_process.start()

    logging.info(u'Starting extraction worker processes.')
    for worker_number in range(number_of_extraction_workers):
      extraction_worker = self.CreateExtractionWorker(worker_number)

      worker_name = u'Worker_{0:d}'.format(worker_number)

      # TODO: Test to see if a process pool can be a better choice.
      worker_process = MultiProcessEventExtractionWorkerProcess(
          extraction_worker, parser_filter_string, hasher_names_string,
          name=worker_name)
      worker_process.start()

      if self._foreman_object:
        self._foreman_object.MonitorWorker(
            pid=worker_process.pid, name=worker_name)

      self._worker_processes[worker_name] = worker_process

    logging.debug(u'Collection started.')
    if not self._collection_process:
      collector_object.Collect()

    else:
      while self._collection_process.is_alive():
        self._collection_process.join(timeout=10)

        # Check the worker status regularly while collection is still ongoing.
        if self._foreman_object:
          self._foreman_object.CheckStatus()

          # TODO: We get a signal when collection is done, which might happen
          # before the collection thread joins. Look at the option of speeding
          # up the process of the collector stopping by potentially killing it.

    logging.info(u'Collection stopped.')

    self._StopProcessing()

  def _StopProcessing(self):
    """Stops the foreman and worker processes."""
    if self._foreman_object:
      self._foreman_object.SignalEndOfProcessing()
      self._StopRPCProxyServerThread()

    # Run through the running workers, one by one.
    # This will go through a list of all active worker processes and check it's
    # status. If a worker has completed it will be removed from the list.
    # The process will not wait longer than five seconds for each worker to
    # complete, if longer time passes it will simply check it's status and
    # move on. That ensures that worker process is monitored and status is
    # updated.
    while self._worker_processes:
      # Note that self._worker_processes is altered in this loop hence we need
      # it to be sorted.
      for process_name, process_obj in sorted(self._worker_processes.items()):
        if self._foreman_object:
          worker_label = self._foreman_object.GetLabel(
              name=process_name, pid=process_obj.pid)
        else:
          worker_label = None

        if not worker_label:
          if process_obj.is_alive():
            logging.info((
                u'Process {0:s} [{1:d}] is not monitored by the foreman. Most '
                u'likely due to a worker having completed it\'s processing '
                u'while waiting for another worker to complete.').format(
                    process_name, process_obj.pid))
            logging.info(
                u'Waiting for worker {0:s} to complete.'.format(process_name))
            process_obj.join()
            logging.info(u'Worker: {0:s} [{1:d}] has completed.'.format(
                process_name, process_obj.pid))

          del self._worker_processes[process_name]
          continue

        if process_obj.is_alive():
          # Check status of worker.
          self._foreman_object.CheckStatus(label=worker_label)
          process_obj.join(timeout=5)

        # Note that we explicitly must test against exitcode 0 here since
        # process.exitcode will be None if there is no exitcode.
        elif process_obj.exitcode != 0:
          logging.warning((
              u'Worker process: {0:s} already exited with code: '
              u'{1:d}.').format(process_name, process_obj.exitcode))
          process_obj.terminate()
          self._foreman_object.TerminateProcess(label=worker_label)

        else:
          # Process is no longer alive, no need to monitor.
          self._foreman_object.StopMonitoringWorker(label=worker_label)
          # Remove it from our list of active workers.
          del self._worker_processes[process_name]

    if self._foreman_object:
      self._foreman_object = None

    logging.info(u'Extraction workers stopped.')
    self._event_queue_producer.SignalEndOfInput()

    self._storage_process.join()
    logging.info(u'Storage writer stopped.')

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
      for _, worker_process in self._worker_processes.iteritems():
        worker_process.SignalAbort()

    logging.warning(u'Signaling storage process to abort.')
    self._event_queue_producer.SignalEndOfInput()
    self._storage_process.SignalAbort()

    if self._collection_process:
      logging.warning(u'Waiting for collection process: {0:d}.'.format(
          self._collection_process.pid))
      # TODO: it looks like xmlrpclib.ServerProxy is not allowing the
      # collection process to close.
      self._collection_process.join(timeout=timeout)

    if self._worker_processes:
      for worker_name, worker_process in self._worker_processes.iteritems():
        logging.warning(u'Waiting for worker: {0:s} process: {1:d}'.format(
            worker_name, worker_process.pid))
        worker_process.join(timeout=timeout)

    if self._storage_process:
      logging.warning(u'Waiting for storage process: {0:d}.'.format(
          self._collection_process.pid))
      self._storage_process.join(timeout=timeout)

  def _AbortTerminate(self):
    """Abort processing by sending SIGTERM or equivalent."""
    if self._collection_process and self._collection_process.is_alive():
      logging.warning(u'Terminating collection process: {0:d}.'.format(
          self._collection_process.pid))
      self._collection_process.terminate()

    if self._worker_processes:
      for worker_name, worker_process in self._worker_processes.iteritems():
        if worker_process.is_alive():
          logging.warning(u'Terminating worker: {0:s} process: {1:d}'.format(
              worker_name, worker_process.pid))
          worker_process.terminate()

    if self._storage_process and self._storage_process.is_alive():
      logging.warning(u'Terminating storage process: {0:d}.'.format(
          self._storage_process.pid))
      self._storage_process.terminate()

  def _AbortKill(self):
    """Abort processing by sending SIGKILL or equivalent."""
    if self._collection_process and self._collection_process.is_alive():
      logging.warning(u'Killing collection process: {0:d}.'.format(
          self._collection_process.pid))
      SigKill(self._collection_process.pid)

    if self._worker_processes:
      for worker_name, worker_process in self._worker_processes.iteritems():
        if worker_process.is_alive():
          logging.warning(u'Killing worker: {0:s} process: {1:d}'.format(
              worker_name, worker_process.pid))
          SigKill(worker_process.pid)

    if self._storage_process and self._storage_process.is_alive():
      logging.warning(u'Killing storage process: {0:d}.'.format(
          self._storage_process.pid))
      SigKill(self._storage_process.pid)

  def SignalAbort(self):
    """Signals the engine to abort."""
    super(MultiProcessEngine, self).SignalAbort()

    try:
      self._AbortNormal(timeout=2)
      self._AbortTerminate()
    except KeyboardInterrupt:
      self._AbortKill()

    # TODO: remove the need for this.
    # Sometimes the main process will be unresponsive.
    SigKill(os.getpid())


class MultiProcessCollectionProcess(multiprocessing.Process):
  """Class that defines a multi-processing collection process."""

  def __init__(self, collector_object, rpc_port_number, **kwargs):
    """Initializes the process object.

    Args:
      collector_object: A collector object (instance of Collector).
      rpc_port_number: An integer value containing the RPC end point port
                       number or 0 if not set.
    """
    super(MultiProcessCollectionProcess, self).__init__(**kwargs)
    self._collector_object = collector_object
    self._rpc_port_number = rpc_port_number

  # This method part of the multiprocessing.Process interface hence its name
  # is not following the style guide.
  def run(self):
    """The main loop."""
    # Prevent the KeyboardInterrupt being raised inside the worker process.
    # This will prevent a collection process to generate a traceback
    # when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    logging.debug(u'Collection process: {0!s} started'.format(self._name))

    rpc_proxy_client = None
    if self._rpc_port_number:
      try:
        rpc_proxy_client = rpc_proxy.StandardRpcProxyClient(
            self._rpc_port_number)
        rpc_proxy_client.Open()

      except errors.ProxyFailedToStart as exception:
        logging.error((
            u'Unable to setup a RPC client for the collector process with '
            u'error {0:s}').format(exception))

    self._collector_object.Collect()

    logging.debug(u'Collection process: {0!s} stopped'.format(self._name))
    if rpc_proxy_client:
      _ = rpc_proxy_client.GetData(u'signal_end_of_collection')

  def SignalAbort(self):
    """Signals the process to abort."""
    self._collector_object.SignalAbort()


class MultiProcessEventExtractionWorkerProcess(multiprocessing.Process):
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
    """
    super(MultiProcessEventExtractionWorkerProcess, self).__init__(**kwargs)
    self._extraction_worker = extraction_worker

    # TODO: clean this up with the implementation of a task based
    # multi-processing approach.
    self._parser_filter_string = parser_filter_string
    self._hasher_names_string = hasher_names_string

    # Attributes for RPC proxy server thread.
    self._proxy_thread = None
    self._rpc_proxy_server = None

  def _StartRPCProxyServerThread(self):
    """Starts the RPC proxy server thread."""
    if self._rpc_proxy_server or self._proxy_thread:
      return

    # Set up a simple XML RPC server for the worker for status indications.
    # Since we don't know the worker's PID for now we'll set the initial port
    # number to zero and then adjust it later.
    self._rpc_proxy_server = rpc_proxy.StandardRpcProxyServer()

    try:
      self._rpc_proxy_server.SetListeningPort(os.getpid())
      self._rpc_proxy_server.Open()
      self._rpc_proxy_server.RegisterFunction(
          'status', self._extraction_worker.GetStatus)

      self._proxy_thread = threading.Thread(
          name='rpc_proxy', target=self._rpc_proxy_server.StartProxy)
      self._proxy_thread.start()

    except errors.ProxyFailedToStart as exception:
      logging.error((
          u'Unable to setup a RPC server for the worker: {0:d} [PID {1:d}] '
          u'with error: {2:s}').format(
              self._identity, os.getpid(), exception))

  def _StopRPCProxyServerThread(self):
    """Stops the RPC proxy server thread."""
    if not self._rpc_proxy_server or not self._proxy_thread:
      return

    # Close the proxy, free up resources so we can shut down the thread.
    self._rpc_proxy_server.Close()

    if self._proxy_thread.isAlive():
      self._proxy_thread.join()

    self._rpc_proxy_server = None
    self._proxy_thread = None

  # This method part of the multiprocessing.Process interface hence its name
  # is not following the style guide.
  def run(self):
    """The main loop."""
    # Prevent the KeyboardInterrupt being raised inside the worker process.
    # This will prevent a worker process generating a traceback
    # when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # We need to initialize the parser and hasher objects after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    self._extraction_worker.InitializeParserObjects(
        parser_filter_string=self._parser_filter_string)
    if self._hasher_names_string:
      self._extraction_worker.SetHashers(self._hasher_names_string)

    logging.debug(u'Worker process: {0!s} started'.format(self._name))
    self._StartRPCProxyServerThread()

    self._extraction_worker.Run()

    logging.debug(u'Worker process: {0!s} stopped'.format(self._name))
    self._StopRPCProxyServerThread()

  def SignalAbort(self):
    """Signals the process to abort."""
    self._extraction_worker.SignalAbort()


class MultiProcessStorageProcess(multiprocessing.Process):
  """Class that defines a multi-processing storage process."""

  def __init__(self, storage_writer, **kwargs):
    """Initializes the process object.

    Args:
      storage_writer: A storage writer object (instance of BaseStorageWriter).
    """
    super(MultiProcessStorageProcess, self).__init__(**kwargs)
    self._storage_writer = storage_writer

  # This method part of the multiprocessing.Process interface hence its name
  # is not following the style guide.
  def run(self):
    """The main loop."""
    # Prevent the KeyboardInterrupt being raised inside the worker process.
    # This will prevent a storage process to generate a traceback
    # when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    logging.debug(u'Storage process: {0!s} started'.format(self._name))
    self._storage_writer.WriteEventObjects()
    logging.debug(u'Storage process: {0!s} stopped'.format(self._name))

  def SignalAbort(self):
    """Signals the process to abort."""
    self._storage_writer.SignalAbort()


class MultiProcessingQueue(queue.Queue):
  """Class that defines the multi-processing queue."""

  def __init__(self, maximum_number_of_queued_items=0):
    """Initializes the multi-processing queue object.

    Args:
      maximum_number_of_queued_items: The maximum number of queued items.
                                      The default is 0, which represents
                                      no limit.
    """
    super(MultiProcessingQueue, self).__init__()

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
    self._queue = multiprocessing.Queue(
        maxsize=maximum_number_of_queued_items)

  def __len__(self):
    """Returns the estimated current number of items in the queue."""
    size = 0
    try:
      size = self._queue.qsize()
    except NotImplementedError:
      logging.warning((
          u'Returning queue length does not work on Mac OS X because of broken '
          u'sem_getvalue()'))
      raise

    return size

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return self._queue.empty()

  def PushItem(self, item):
    """Pushes an item onto the queue."""
    self._queue.put(item)

  def PopItem(self):
    """Pops an item off the queue."""
    try:
      return self._queue.get()
    except KeyboardInterrupt:
      raise errors.QueueEmpty
