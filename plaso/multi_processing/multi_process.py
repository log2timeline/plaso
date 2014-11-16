#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The multi-process processing engine."""

import logging
import multiprocessing
import os
import threading

from plaso.engine import collector
from plaso.engine import engine
from plaso.engine import queue
from plaso.engine import worker
from plaso.lib import errors
from plaso.multi_processing import foreman
from plaso.multi_processing import rpc_proxy
from plaso.parsers import context as parsers_context


class MultiProcessCollector(collector.Collector):
  """Class that implements a multi-process collector object."""

  def __init__(
      self, process_queue, source_path, source_path_spec,
      resolver_context=None):
    """Initializes the multi-process collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      process_queue: The process queue (instance of Queue). This queue contains
                     the file entries that need to be processed.
      source_path: Path of the source file or directory.
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None.
    """
    super(MultiProcessCollector, self).__init__(
        process_queue, source_path, source_path_spec,
        resolver_context=resolver_context)

    self._rpc_proxy_client = None

  def Collect(self):
    """Collects files from the source."""
    if self._rpc_proxy_client:
      self._rpc_proxy_client.Open()

    super(MultiProcessCollector, self).Collect()

    if self._rpc_proxy_client:
      # Send the notification.
      _ = self._rpc_proxy_client.GetData(u'signal_end_of_collection')

  def SetProxy(self, rpc_proxy_client):
    """Sets the RPC proxy the collector should use.

    Args:
      rpc_proxy_client: A RPC proxy client object (instance of ProxyClient).
    """
    self._rpc_proxy_client = rpc_proxy_client


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
    self._storage_process = None

    # TODO: turn into a process pool.
    self._worker_processes = {}

    # Attributes for RPC proxy server thread.
    self._proxy_thread = None
    self._rpc_proxy_server = None

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

    self._rpc_proxy_server = None
    self._proxy_thread = None

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

    collector_object = MultiProcessCollector(
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
    parser_context = parsers_context.ParserContext(
        self._event_queue_producer, self._parse_error_queue_producer,
        self.knowledge_base)

    extraction_worker = MultiProcessEventExtractionWorker(
        worker_number, self._collection_queue, self._event_queue_producer,
        self._parse_error_queue_producer, parser_context)

    extraction_worker.SetEnableDebugOutput(self._enable_debug_output)

    # TODO: move profiler in separate object.
    extraction_worker.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate)

    if self._open_files:
      extraction_worker.SetOpenFiles(self._open_files)

    if self._filter_object:
      extraction_worker.SetFilterObject(self._filter_object)

    if self._mount_path:
      extraction_worker.SetMountPath(self._mount_path)

    if self._text_prepend:
      extraction_worker.SetTextPrepend(self._text_prepend)

    return extraction_worker

  def ProcessSource(
      self, collector_object, storage_writer, parser_filter_string=None,
      number_of_extraction_workers=0, have_collection_process=True,
      have_foreman_process=True, show_memory_usage=False):
    """Processes the source and extracts event objects.

    Args:
      collector_object: A collector object (instance of Collector).
      storage_writer: A storage writer object (instance of BaseStorageWriter).
      parser_filter_string: Optional parser filter string. The default is None.
      number_of_extraction_workers: Optional number of extraction worker
                                    processes. The default is 0 which means
                                    the function will determine the suitable
                                    number.
      have_collection_process: Optional boolean value to indidate a separate
                               collection process should be run. The default
                               is true.
      have_foreman_process: Optional boolean value to indidate a separate
                            foreman process should be run to make sure the
                            workers are extracting event objects. The default
                            is true.
      show_memory_usage: Optional boolean value to indicate memory information
                         should be included in logging. The default is false.
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

    foreman_object = None
    rpc_proxy_client = None

    if have_foreman_process:
      foreman_object = foreman.Foreman(show_memory_usage=show_memory_usage)
      self._StartRPCProxyServerThread(foreman_object)

      try:
        rpc_proxy_client = rpc_proxy.StandardRpcProxyClient(
            self._rpc_proxy_server.listening_port)

        collector_object.SetProxy(rpc_proxy_client)

      except errors.ProxyFailedToStart as exception:
        logging.error((
            u'Unable to setup a RPC client for the engine with error '
            u'{0:s}').format(exception))

    logging.info(u'Starting storage process.')
    self._storage_process = multiprocessing.Process(
        name='StorageProcess', target=storage_writer.WriteEventObjects)
    self._storage_process.start()

    if have_collection_process:
      logging.info(u'Starting collection process.')
      self._collection_process = multiprocessing.Process(
          name='CollectionProcess', target=collector_object.Collect)
      self._collection_process.start()

    logging.info(u'Starting extraction worker processes.')
    for worker_number in range(number_of_extraction_workers):
      extraction_worker = self.CreateExtractionWorker(worker_number)

      # TODO: clean this up with the implementation of a task based
      # multi-processing approach.
      extraction_worker.parser_filter_string = parser_filter_string

      worker_name = u'Worker_{0:d}'.format(worker_number)

      # TODO: Test to see if a process pool can be a better choice.
      logging.debug(u'Starting worker: {0:d} process'.format(worker_number))
      worker_process = multiprocessing.Process(
          name=worker_name, target=extraction_worker.Run)
      worker_process.start()

      if have_foreman_process:
        foreman_object.MonitorWorker(pid=worker_process.pid, name=worker_name)

      self._worker_processes[worker_name] = worker_process

    logging.debug(u'Collection started.')
    if not self._collection_process:
      collector_object.Collect()

    else:
      while self._collection_process.is_alive():
        self._collection_process.join(10)

        # Check the worker status regularly while collection is still ongoing.
        if have_foreman_process:
          foreman_object.CheckStatus()

          # TODO: We get a signal when collection is done, which might happen
          # before the collection thread joins. Look at the option of speeding
          # up the process of the collector stopping by potentially killing it.

    logging.info(u'Collection stopped.')

    if have_foreman_process:
      foreman_object.SignalEndOfProcessing()
      self._StopRPCProxyServerThread()

    # Run through the running workers, one by one.
    # This will go through a list of all active worker processes and check it's
    # status. If a worker has completed it will be removed from the list.
    # The process will not wait longer than five seconds for each worker to
    # complete, if longer time passes it will simply check it's status and
    # move on. That ensures that worker process is monitored and status is
    # updated.
    while self._worker_processes:
      for process_name, process_obj in sorted(self._worker_processes.items()):
        if have_foreman_process:
          worker_label = foreman_object.GetLabel(
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
          foreman_object.CheckStatus(label=worker_label)
          process_obj.join(5)
        # Note that we explicitly must test against exitcode 0 here since
        # process.exitcode will be None if there is no exitcode.
        elif process_obj.exitcode != 0:
          logging.warning((
              u'Worker process: {0:s} already exited with code: '
              u'{1:d}.').format(process_name, process_obj.exitcode))
          process_obj.terminate()
          foreman_object.TerminateProcess(label=worker_label)

        else:
          # Process is no longer alive, no need to monitor.
          foreman_object.StopMonitoringWorker(label=worker_label)
          # Remove it from our list of active workers.
          del self._worker_processes[process_name]

    logging.info(u'Extraction workers stopped.')
    self._event_queue_producer.SignalEndOfInput()

    self._storage_process.join()
    logging.info(u'Storage writer stopped.')


class MultiProcessEventExtractionWorker(worker.BaseEventExtractionWorker):
  """Class that defines the multi-process event extraction worker."""

  def __init__(
      self, identifier, process_queue, event_queue_producer,
      parse_error_queue_producer, parser_context):
    """Initializes the event extraction worker object.

    Args:
      identifier: A thread identifier, usually an incrementing integer.
      process_queue: The process queue (instance of Queue). This queue contains
                     the file entries that need to be processed.
      event_queue_producer: The event object queue producer (instance of
                            ItemQueueProducer).
      parse_error_queue_producer: The parse error queue producer (instance of
                                  ItemQueueProducer).
      parser_context: A parser context object (instance of ParserContext).
    """
    super(MultiProcessEventExtractionWorker, self).__init__(
        identifier, process_queue, event_queue_producer,
        parse_error_queue_producer, parser_context)

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
      self._rpc_proxy_server.RegisterFunction('status', self.GetStatus)

      self._proxy_thread = threading.Thread(
          name='rpc_proxy', target=self._rpc_proxy_server.StartProxy)
      self._proxy_thread.start()

    except errors.ProxyFailedToStart as exception:
      logging.error((
          u'Unable to setup a RPC server for the worker: {0:d} [PID {1:d}] '
          u'with error: {2:s}').format(
              self._identifier, os.getpid(), exception))

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

  def Run(self):
    """Extracts event objects from file entries."""
    self._StartRPCProxyServerThread()

    # We need to initialize the parser object after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    if not self._parser_objects:
      self.InitalizeParserObjects(
          parser_filter_string=self.parser_filter_string)

    super(MultiProcessEventExtractionWorker, self).Run()

    self._StopRPCProxyServerThread()


class MultiProcessingQueue(queue.Queue):
  """Multi-processing queue."""

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
