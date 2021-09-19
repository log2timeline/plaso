# -*- coding: utf-8 -*-
"""The task-based multi-process processing analysis engine."""

import collections
import os
import time

from plaso.containers import events
from plaso.containers import tasks
from plaso.engine import processing_status
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_process import analysis_process
from plaso.multi_process import logger
from plaso.multi_process import plaso_queue
from plaso.multi_process import task_engine
from plaso.multi_process import zeromq_queue
from plaso.storage import event_tag_index


class AnalysisMultiProcessEngine(task_engine.TaskMultiProcessEngine):
  """Task-based multi-process analysis engine.

  This class contains functionality to:
  * monitor and manage analysis tasks;
  * merge results returned by analysis worker processes.
  """

  # pylint: disable=abstract-method

  _PROCESS_JOIN_TIMEOUT = 5.0

  _QUEUE_TIMEOUT = 10 * 60

  def __init__(self, worker_memory_limit=None, worker_timeout=None):
    """Initializes a task-based multi-process analysis engine.

    Args:
      worker_memory_limit (Optional[int]): maximum amount of memory a worker is
          allowed to consume, where None represents the default memory limit
          and 0 represents no limit.
      worker_timeout (Optional[float]): number of minutes before a worker
          process that is not providing status updates is considered inactive,
          where None or 0.0 represents the default timeout.
    """
    if worker_memory_limit is None:
      worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

    super(AnalysisMultiProcessEngine, self).__init__()
    self._analysis_plugins = {}
    self._completed_analysis_processes = set()
    self._data_location = None
    self._event_filter_expression = None
    self._event_queues = {}
    self._events_status = processing_status.EventsStatus()
    self._event_tag_index = event_tag_index.EventTagIndex()
    self._knowledge_base = None
    self._memory_profiler = None
    self._merge_task = None
    self._number_of_consumed_analysis_reports = 0
    self._number_of_consumed_analysis_warnings = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_analysis_reports = 0
    self._number_of_produced_analysis_warnings = 0
    self._number_of_produced_events = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_sources = 0
    self._processing_profiler = None
    self._serializers_profiler = None
    self._session = None
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._status_update_callback = None
    self._worker_memory_limit = worker_memory_limit
    self._worker_timeout = worker_timeout or definitions.DEFAULT_WORKER_TIMEOUT

  def _AnalyzeEvents(self, storage_writer, analysis_plugins, event_filter=None):
    """Analyzes events in a Plaso storage.

    Args:
      storage_writer (StorageWriter): storage writer.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
      event_filter (Optional[EventObjectFilter]): event filter.

    Returns:
      collections.Counter: counter containing information about the events
          processed and filtered.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    self._status = definitions.STATUS_INDICATOR_RUNNING
    self._number_of_consumed_analysis_reports = 0
    self._number_of_consumed_analysis_warnings = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_analysis_reports = 0
    self._number_of_produced_analysis_warnings = 0
    self._number_of_produced_events = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_sources = 0

    number_of_filtered_events = 0

    logger.debug('Processing events.')

    filter_limit = getattr(event_filter, 'limit', None)

    for event in storage_writer.GetSortedEvents():
      event_data_identifier = event.GetEventDataIdentifier()
      event_data = storage_writer.GetAttributeContainerByIdentifier(
          events.EventData.CONTAINER_TYPE, event_data_identifier)

      event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
      if event_data_stream_identifier:
        event_data_stream = storage_writer.GetAttributeContainerByIdentifier(
            events.EventDataStream.CONTAINER_TYPE, event_data_stream_identifier)
      else:
        event_data_stream = None

      event_identifier = event.GetIdentifier()
      event_tag = self._event_tag_index.GetEventTagByIdentifier(
          storage_writer, event_identifier)

      if event_filter:
        filter_match = event_filter.Match(
            event, event_data, event_data_stream, event_tag)
      else:
        filter_match = None

      # pylint: disable=singleton-comparison
      if filter_match == False:
        number_of_filtered_events += 1
        continue

      for event_queue in self._event_queues.values():
        # TODO: Check for premature exit of analysis plugins.
        event_queue.PushItem((event, event_data, event_data_stream))

      self._number_of_consumed_events += 1

      if (event_filter and filter_limit and
          filter_limit == self._number_of_consumed_events):
        break

    logger.debug('Finished pushing events to analysis plugins.')
    # Signal that we have finished adding events.
    for event_queue in self._event_queues.values():
      event_queue.PushItem(plaso_queue.QueueAbort(), block=False)

    logger.debug('Processing analysis plugin results.')

    # TODO: use a task based approach.
    plugin_names = list(analysis_plugins.keys())
    while plugin_names:
      for plugin_name in list(plugin_names):
        if self._abort:
          break

        # TODO: temporary solution.
        task = tasks.Task()
        task.storage_format = definitions.STORAGE_FORMAT_SQLITE
        task.identifier = plugin_name

        merge_ready = self._CheckTaskReadyForMerge(
            definitions.STORAGE_FORMAT_SQLITE, task)
        if merge_ready:
          self._PrepareMergeTaskStorage(definitions.STORAGE_FORMAT_SQLITE, task)
          self._status = definitions.STATUS_INDICATOR_MERGING

          event_queue = self._event_queues[plugin_name]
          del self._event_queues[plugin_name]

          event_queue.Close()

          storage_merge_reader = self._StartMergeTaskStorage(
              self._session, storage_writer, definitions.STORAGE_FORMAT_SQLITE,
              task)

          storage_merge_reader.MergeAttributeContainers()
          # TODO: temporary solution.
          plugin_names.remove(plugin_name)

          storage_merge_reader.Close()

          self._RemoveMergeTaskStorage(
              definitions.STORAGE_FORMAT_SQLITE, task)

          self._status = definitions.STATUS_INDICATOR_RUNNING

          self._number_of_produced_event_tags = (
              storage_writer.number_of_event_tags)
          self._number_of_produced_analysis_reports = (
              storage_writer.number_of_analysis_reports)

    events_counter = collections.Counter()
    events_counter['Events filtered'] = number_of_filtered_events
    events_counter['Events processed'] = self._number_of_consumed_events

    return events_counter

  def _CheckStatusAnalysisProcess(self, pid):
    """Checks the status of an analysis process.

    Args:
      pid (int): process ID (PID) of a registered analysis process.

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    # TODO: Refactor this method, simplify and separate concerns (monitoring
    # vs management).
    self._RaiseIfNotRegistered(pid)

    if pid in self._completed_analysis_processes:
      status_indicator = definitions.STATUS_INDICATOR_COMPLETED
      process_status = {
          'processing_status': status_indicator}
      used_memory = 0

    else:
      process = self._processes_per_pid[pid]

      process_status = self._QueryProcessStatus(process)
      if process_status is None:
        process_is_alive = False
      else:
        process_is_alive = True

      process_information = self._process_information_per_pid[pid]
      used_memory = process_information.GetUsedMemory() or 0

      if self._worker_memory_limit and used_memory > self._worker_memory_limit:
        logger.warning((
            'Process: {0:s} (PID: {1:d}) killed because it exceeded the '
            'memory limit: {2:d}.').format(
                process.name, pid, self._worker_memory_limit))
        self._KillProcess(pid)

      if isinstance(process_status, dict):
        self._rpc_errors_per_pid[pid] = 0
        status_indicator = process_status.get('processing_status', None)

        if status_indicator == definitions.STATUS_INDICATOR_COMPLETED:
          self._completed_analysis_processes.add(pid)

      else:
        rpc_errors = self._rpc_errors_per_pid.get(pid, 0) + 1
        self._rpc_errors_per_pid[pid] = rpc_errors

        if rpc_errors > self._MAXIMUM_RPC_ERRORS:
          process_is_alive = False

        if process_is_alive:
          rpc_port = process.rpc_port.value
          logger.warning((
              'Unable to retrieve process: {0:s} (PID: {1:d}) status via '
              'RPC socket: http://localhost:{2:d}').format(
                  process.name, pid, rpc_port))

          processing_status_string = 'RPC error'
          status_indicator = definitions.STATUS_INDICATOR_RUNNING
        else:
          processing_status_string = 'killed'
          status_indicator = definitions.STATUS_INDICATOR_KILLED

        process_status = {
            'processing_status': processing_status_string}

    self._UpdateProcessingStatus(pid, process_status, used_memory)

    if status_indicator in definitions.ERROR_STATUS_INDICATORS:
      logger.error((
          'Process {0:s} (PID: {1:d}) is not functioning correctly. '
          'Status code: {2!s}.').format(
              process.name, pid, status_indicator))

      self._TerminateProcessByPid(pid)

  def _StartAnalysisProcesses(self, analysis_plugins):
    """Starts the analysis processes.

    Args:
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
    """
    logger.info('Starting analysis plugins.')

    for analysis_plugin in analysis_plugins.values():
      self._analysis_plugins[analysis_plugin.NAME] = analysis_plugin

      process = self._StartWorkerProcess(analysis_plugin.NAME)
      if not process:
        logger.error('Unable to create analysis process: {0:s}'.format(
            analysis_plugin.NAME))

    logger.info('Analysis plugins running')

  def _StartWorkerProcess(self, process_name):
    """Creates, starts, monitors and registers a worker process.

    Args:
      process_name (str): process name.

    Returns:
      MultiProcessWorkerProcess: extraction worker process or None on error.
    """
    analysis_plugin = self._analysis_plugins.get(process_name, None)
    if not analysis_plugin:
      logger.error('Missing analysis plugin: {0:s}'.format(process_name))
      return None

    queue_name = '{0:s} output event queue'.format(process_name)
    output_event_queue = zeromq_queue.ZeroMQPushBindQueue(
        name=queue_name, timeout_seconds=self._QUEUE_TIMEOUT)
    # Open the queue so it can bind to a random port, and we can get the
    # port number to use in the input queue.
    output_event_queue.Open()

    self._event_queues[process_name] = output_event_queue

    queue_name = '{0:s} input event queue'.format(process_name)
    input_event_queue = zeromq_queue.ZeroMQPullConnectQueue(
        name=queue_name, delay_open=True, port=output_event_queue.port,
        timeout_seconds=self._QUEUE_TIMEOUT)

    process = analysis_process.AnalysisProcess(
        input_event_queue, self._knowledge_base, self._session, analysis_plugin,
        self._processing_configuration, data_location=self._data_location,
        event_filter_expression=self._event_filter_expression,
        name=process_name)

    process.start()

    logger.info('Started analysis plugin: {0:s} (PID: {1:d}).'.format(
        process_name, process.pid))

    try:
      self._StartMonitoringProcess(process)
    except (IOError, KeyError) as exception:
      logger.error((
          'Unable to monitor analysis plugin: {0:s} (PID: {1:d}) '
          'with error: {2!s}').format(process_name, process.pid, exception))

      process.terminate()
      return None

    self._RegisterProcess(process)
    return process

  def _StopAnalysisProcesses(self, abort=False):
    """Stops the analysis processes.

    Args:
      abort (bool): True to indicated the stop is issued on abort.
    """
    logger.debug('Stopping analysis processes.')
    self._StopMonitoringProcesses()

    if abort:
      # Signal all the processes to abort.
      self._AbortTerminate()

    # Wake the processes to make sure that they are not blocking
    # waiting for the queue new items.
    for event_queue in self._event_queues.values():
      event_queue.PushItem(plaso_queue.QueueAbort(), block=False)

    # Try waiting for the processes to exit normally.
    self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)
    for event_queue in self._event_queues.values():
      event_queue.Close(abort=abort)

    if abort:
      # Kill any remaining processes.
      self._AbortKill()
    else:
      # Check if the processes are still alive and terminate them if necessary.
      self._AbortTerminate()
      self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)

      for event_queue in self._event_queues.values():
        event_queue.Close(abort=True)

  def _UpdateForemanProcessStatus(self):
    """Update the foreman process status."""
    used_memory = self._process_information.GetUsedMemory() or 0

    display_name = getattr(self._merge_task, 'identifier', '')

    self._processing_status.UpdateForemanStatus(
        self._name, self._status, self._pid, used_memory, display_name,
        self._number_of_consumed_sources, self._number_of_produced_sources,
        self._number_of_consumed_events, self._number_of_produced_events,
        self._number_of_consumed_event_tags,
        self._number_of_produced_event_tags,
        self._number_of_consumed_analysis_reports,
        self._number_of_produced_analysis_reports,
        self._number_of_consumed_analysis_warnings,
        self._number_of_produced_analysis_warnings)

    self._processing_status.UpdateEventsStatus(self._events_status)

  def _UpdateProcessingStatus(self, pid, process_status, used_memory):
    """Updates the processing status.

    Args:
      pid (int): process identifier (PID) of the worker process.
      process_status (dict[str, object]): status values received from
          the worker process.
      used_memory (int): size of used memory in bytes.

    Raises:
      KeyError: if the process is not registered with the engine.
    """
    self._RaiseIfNotRegistered(pid)

    if not process_status:
      return

    process = self._processes_per_pid[pid]

    status_indicator = process_status.get('processing_status', None)

    self._RaiseIfNotMonitored(pid)

    display_name = process_status.get('display_name', '')

    number_of_consumed_analysis_warnings = process_status.get(
        'number_of_consumed_analysis_warnings', None)
    number_of_produced_analysis_warnings = process_status.get(
        'number_of_produced_analysis_warnings', None)

    number_of_consumed_event_tags = process_status.get(
        'number_of_consumed_event_tags', None)
    number_of_produced_event_tags = process_status.get(
        'number_of_produced_event_tags', None)

    number_of_consumed_events = process_status.get(
        'number_of_consumed_events', None)
    number_of_produced_events = process_status.get(
        'number_of_produced_events', None)

    number_of_consumed_reports = process_status.get(
        'number_of_consumed_reports', None)
    number_of_produced_reports = process_status.get(
        'number_of_produced_reports', None)

    number_of_consumed_sources = process_status.get(
        'number_of_consumed_sources', None)
    number_of_produced_sources = process_status.get(
        'number_of_produced_sources', None)

    if status_indicator != definitions.STATUS_INDICATOR_IDLE:
      last_activity_timestamp = process_status.get(
          'last_activity_timestamp', 0.0)

      if last_activity_timestamp:
        last_activity_timestamp += self._worker_timeout

        current_timestamp = time.time()
        if current_timestamp > last_activity_timestamp:
          logger.error((
              'Process {0:s} (PID: {1:d}) has not reported activity within '
              'the timeout period.').format(process.name, pid))
          status_indicator = definitions.STATUS_INDICATOR_NOT_RESPONDING

    self._processing_status.UpdateWorkerStatus(
        process.name, status_indicator, pid, used_memory, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_event_tags, number_of_produced_event_tags,
        number_of_consumed_reports, number_of_produced_reports,
        number_of_consumed_analysis_warnings,
        number_of_produced_analysis_warnings)

  def _UpdateStatus(self):
    """Update the status."""
    # Make a local copy of the PIDs in case the dict is changed by
    # the main thread.
    for pid in list(self._process_information_per_pid.keys()):
      self._CheckStatusAnalysisProcess(pid)

    self._UpdateForemanProcessStatus()

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  # pylint: disable=too-many-arguments
  def AnalyzeEvents(
      self, session, knowledge_base_object, storage_writer, data_location,
      analysis_plugins, processing_configuration, event_filter=None,
      event_filter_expression=None, status_update_callback=None,
      storage_file_path=None):
    """Analyzes events in a Plaso storage.

    Args:
      session (Session): session in which the events are analyzed.
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_writer (StorageWriter): storage writer.
      data_location (str): path to the location that data files should
          be loaded from.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      event_filter (Optional[EventObjectFilter]): event filter.
      event_filter_expression (Optional[str]): event filter expression.
      status_update_callback (Optional[function]): callback function for status
          updates.
      storage_file_path (Optional[str]): path to the session storage file.

    Raises:
      KeyboardInterrupt: if a keyboard interrupt was raised.
    """
    if not analysis_plugins:
      return

    abort_kill = False
    keyboard_interrupt = False
    queue_full = False

    self._analysis_plugins = {}
    self._data_location = data_location
    self._event_filter_expression = event_filter_expression
    self._events_status = processing_status.EventsStatus()
    self._knowledge_base = knowledge_base_object
    self._processing_configuration = processing_configuration
    self._session = session
    self._status_update_callback = status_update_callback
    self._storage_file_path = storage_file_path

    total_number_of_events = 0
    for stored_session in storage_writer.GetSessions():
      total_number_of_events += stored_session.parsers_counter['total']

    self._events_status.total_number_of_events = total_number_of_events

    # Set up the storage writer before the analysis processes.
    self._StartTaskStorage(definitions.STORAGE_FORMAT_SQLITE)

    self._StartAnalysisProcesses(analysis_plugins)

    self._StartProfiling(self._processing_configuration.profiling)

    # Start the status update thread after open of the storage writer
    # so we don't have to clean up the thread if the open fails.
    self._StartStatusUpdateThread()

    try:
      storage_writer.WriteSessionStart(session)

      try:
        storage_writer.WriteSessionConfiguration(self._session)

        self._AnalyzeEvents(
            storage_writer, analysis_plugins, event_filter=event_filter)

        self._status = definitions.STATUS_INDICATOR_FINALIZING

      except errors.QueueFull:
        queue_full = True
        self._abort = True

      except KeyboardInterrupt:
        keyboard_interrupt = True
        self._abort = True

      finally:
        self._processing_status.aborted = self._abort
        self._session.aborted = self._abort
        storage_writer.WriteSessionCompletion(self._session)

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

      self._StopProfiling()

    # Update the status view one last time before the analysis processses are
    # stopped.
    self._UpdateStatus()

    if queue_full:
      # TODO: handle abort on queue full more elegant.
      abort_kill = True
    else:
      try:
        self._StopAnalysisProcesses(abort=self._abort)

      except KeyboardInterrupt:
        keyboard_interrupt = True
        abort_kill = True

    if abort_kill:
      self._AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrectly finalized IPC.
      self._KillProcess(os.getpid())

    try:
      self._StopTaskStorage(
          definitions.STORAGE_FORMAT_SQLITE, self._session.identifier,
          abort=self._abort)
    except (IOError, OSError) as exception:
      logger.error('Unable to stop task storage with error: {0!s}'.format(
          exception))

    if self._abort:
      logger.debug('Analysis aborted.')
    else:
      logger.debug('Analysis completed.')

    # Update the status view one last time.
    self._UpdateStatus()

    # Reset values.
    self._analysis_plugins = {}
    self._data_location = None
    self._event_filter_expression = None
    self._knowledge_base = None
    self._processing_configuration = None
    self._session = None
    self._status_update_callback = None
    self._storage_file_path = None

    if keyboard_interrupt:
      raise KeyboardInterrupt
