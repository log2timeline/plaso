# -*- coding: utf-8 -*-
"""The psort multi-processing engine."""

import collections
import heapq
import logging
import os
import time

from plaso.engine import plaso_queue
from plaso.engine import zeromq_queue
from plaso.containers import tasks
from plaso.lib import bufferlib
from plaso.lib import definitions
from plaso.multi_processing import analysis_process
from plaso.multi_processing import engine as multi_process_engine
from plaso.multi_processing import multi_process_queue
from plaso.storage import time_range as storage_time_range


class PsortEventHeap(object):
  """Psort event heap."""

  _IDENTIFIER_EXCLUDED_ATTRIBUTES = frozenset([
      u'data_type',
      u'display_name',
      u'filename',
      u'inode',
      u'parser',
      u'tag',
      u'timestamp',
      u'timestamp_desc'])

  def __init__(self):
    """Initializes a psort events heap."""
    super(PsortEventHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of events on the heap."""
    return len(self._heap)

  def _GetEventIdentifiers(self, event):
    """Retrieves different identifiers of the event.

    Every event contains event data, which consists of attributes and values.
    These attributes and values can be represented as a string and used for
    sorting and uniquely identifying events. This function determines multiple
    identifiers:
    * an identifier of the attributes and values without the timestamp
      description (or usage). This is referred to as the MACB group
      identifier.
    * an identifier of the attributes and values including the timestamp
      description (or usage). This is referred to as the event content
      identifier.

    The identifier without the timestamp description can be used to group
    events that have the same MACB (modification, access, change, birth)
    timestamps. The PsortEventHeap will store these events individually and
    relies on PsortMultiProcessEngine to do the actual grouping of events.

    Args:
      event (EventObject): event.

    Returns:
      tuple: contains:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
    """
    attributes = []

    attribute_string = u'data_type: {0:s}'.format(event.data_type)
    attributes.append(attribute_string)

    for attribute_name, attribute_value in sorted(event.GetAttributes()):
      if attribute_name in self._IDENTIFIER_EXCLUDED_ATTRIBUTES:
        continue

      if not attribute_value:
        continue

      if attribute_name == u'pathspec':
        attribute_value = attribute_value.comparable

      elif isinstance(attribute_value, dict):
        attribute_value = sorted(attribute_value.items())

      elif isinstance(attribute_value, set):
        attribute_value = sorted(list(attribute_value))

      attribute_string = u'{0:s}: {1!s}'.format(
          attribute_name, attribute_value)
      attributes.append(attribute_string)

    # The u'atime', u'ctime', u'crtime', u'mtime' are included for backwards
    # compatibility with the filestat parser.
    if event.timestamp_desc in (
        u'atime', u'ctime', u'crtime', u'mtime',
        definitions.TIME_DESCRIPTION_LAST_ACCESS,
        definitions.TIME_DESCRIPTION_CHANGE,
        definitions.TIME_DESCRIPTION_CREATION,
        definitions.TIME_DESCRIPTION_MODIFICATION):
      macb_group_identifier = u', '.join(attributes)
    else:
      macb_group_identifier = None

    attributes.insert(0, event.timestamp_desc)
    content_identifier = u', '.join(attributes)

    return macb_group_identifier, content_identifier

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      tuple: contains:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
        EventObject: event.
    """
    try:
      return heapq.heappop(self._heap)

    except IndexError:
      return None

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      EventObject: event.
    """
    event = self.PopEvent()
    while event:
      yield event
      event = self.PopEvent()

  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """
    macb_group_identifier, content_identifier = self._GetEventIdentifiers(event)

    # We can ignore the timestamp here because the psort engine only stores
    # events with the same timestamp in the event heap.
    heap_values = (macb_group_identifier, content_identifier, event)
    heapq.heappush(self._heap, heap_values)


class PsortMultiProcessEngine(multi_process_engine.MultiProcessEngine):
  """Psort multi-processing engine."""

  _PROCESS_JOIN_TIMEOUT = 5.0
  _PROCESS_WORKER_TIMEOUT = 15.0 * 60.0

  _QUEUE_TIMEOUT = 10 * 60

  def __init__(self, use_zeromq=True):
    """Initializes an engine object.

    Args:
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing
          instead of Python's multiprocessing queue.
    """
    super(PsortMultiProcessEngine, self).__init__()
    self._analysis_plugins = {}
    self._completed_analysis_processes = set()
    self._data_location = None
    self._event_filter_expression = None
    self._event_queues = {}
    # The event heap is used to make sure the events are sorted in
    # a deterministic way.
    self._export_event_heap = PsortEventHeap()
    self._export_event_timestamp = 0
    self._knowledge_base = None
    self._merge_task = None
    self._number_of_consumed_errors = 0
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_duplicate_events = 0
    self._number_of_macb_grouped_events = 0
    self._number_of_produced_errors = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0
    self._status = definitions.PROCESSING_STATUS_IDLE
    self._status_update_callback = None
    self._use_zeromq = use_zeromq
    self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

  def _AnalyzeEvents(self, storage_writer, analysis_plugins, event_filter=None):
    """Analyzes events in a plaso storage.

    Args:
      storage_writer (StorageWriter): storage writer.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
      event_filter (Optional[FilterObject]): event filter.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    self._status = definitions.PROCESSING_STATUS_RUNNING
    self._number_of_consumed_errors = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_errors = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0

    number_of_filtered_events = 0

    logging.debug(u'Processing events.')

    filter_limit = getattr(event_filter, u'limit', None)

    for event in storage_writer.GetSortedEvents():
      if event_filter:
        filter_match = event_filter.Match(event)
      else:
        filter_match = None

      # pylint: disable=singleton-comparison
      if filter_match == False:
        number_of_filtered_events += 1
        continue

      for event_queue in self._event_queues.values():
        # TODO: Check for premature exit of analysis plugins.
        event_queue.PushItem(event)

      self._number_of_consumed_events += 1

      if (event_filter and filter_limit and
          filter_limit == self._number_of_consumed_events):
        break

    logging.debug(u'Finished pushing events to analysis plugins.')
    # Signal that we have finished adding events.
    for event_queue in self._event_queues.values():
      event_queue.PushItem(plaso_queue.QueueAbort(), block=False)

    logging.debug(u'Processing analysis plugin results.')

    # TODO: use a task based approach.
    plugin_names = [plugin_name for plugin_name in analysis_plugins.keys()]
    while plugin_names:
      for plugin_name in list(plugin_names):
        if self._abort:
          break

        # TODO: temporary solution.
        task = tasks.Task()
        task.identifier = plugin_name

        merge_ready = storage_writer.CheckTaskReadyForMerge(task)
        if merge_ready:
          self._status = definitions.PROCESSING_STATUS_MERGING

          event_queue = self._event_queues[plugin_name]
          del self._event_queues[plugin_name]

          event_queue.Close()

          storage_merge_reader = storage_writer.StartMergeTaskStorage(task)

          storage_merge_reader.MergeAttributeContainers()
          # TODO: temporary solution.
          plugin_names.remove(plugin_name)

          self._status = definitions.PROCESSING_STATUS_RUNNING

          self._number_of_produced_event_tags = (
              storage_writer.number_of_event_tags)
          self._number_of_produced_reports = (
              storage_writer.number_of_analysis_reports)

    try:
      storage_writer.StopTaskStorage(abort=self._abort)
    except (IOError, OSError) as exception:
      logging.error(u'Unable to stop task storage with error: {0:s}'.format(
          exception))

    if self._abort:
      logging.debug(u'Processing aborted.')
    else:
      logging.debug(u'Processing completed.')

    events_counter = collections.Counter()
    events_counter[u'Events filtered'] = number_of_filtered_events
    events_counter[u'Events processed'] = self._number_of_consumed_events

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
      status_indicator = definitions.PROCESSING_STATUS_COMPLETED
      process_status = {
          u'processing_status': status_indicator}
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

      if used_memory > self._worker_memory_limit:
        logging.warning((
            u'Process: {0:s} (PID: {1:d}) killed because it exceeded the '
            u'memory limit: {2:d}.').format(
                process.name, pid, self._worker_memory_limit))
        self._KillProcess(pid)

      if isinstance(process_status, dict):
        self._rpc_errors_per_pid[pid] = 0
        status_indicator = process_status.get(u'processing_status', None)

        if status_indicator == definitions.PROCESSING_STATUS_COMPLETED:
          self._completed_analysis_processes.add(pid)

      else:
        rpc_errors = self._rpc_errors_per_pid.get(pid, 0) + 1
        self._rpc_errors_per_pid[pid] = rpc_errors

        if rpc_errors > self._MAXIMUM_RPC_ERRORS:
          process_is_alive = False

        if process_is_alive:
          rpc_port = process.rpc_port.value
          logging.warning((
              u'Unable to retrieve process: {0:s} (PID: {1:d}) status via '
              u'RPC socket: http://localhost:{2:d}').format(
                  process.name, pid, rpc_port))

          processing_status_string = u'RPC error'
          status_indicator = definitions.PROCESSING_STATUS_RUNNING
        else:
          processing_status_string = u'killed'
          status_indicator = definitions.PROCESSING_STATUS_KILLED

        process_status = {
            u'processing_status': processing_status_string}

    self._UpdateProcessingStatus(pid, process_status, used_memory)

    if status_indicator in definitions.PROCESSING_ERROR_STATUS:
      logging.error((
          u'Process {0:s} (PID: {1:d}) is not functioning correctly. '
          u'Status code: {2!s}.').format(
              process.name, pid, status_indicator))

      self._TerminateProcess(pid)

  def _ExportEvent(self, output_module, event, deduplicate_events=True):
    """Exports an event using an output module.

    Args:
      output_module (OutputModule): output module.
      event (EventObject): event.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
    """
    if event.timestamp != self._export_event_timestamp:
      self._FlushExportBuffer(
          output_module, deduplicate_events=deduplicate_events)
      self._export_event_timestamp = event.timestamp

    self._export_event_heap.PushEvent(event)

  def _ExportEvents(
      self, storage_reader, output_module, deduplicate_events=True,
      event_filter=None, time_slice=None, use_time_slicer=False):
    """Exports events using an output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      event_filter (Optional[FilterObject]): event filter.
      time_slice (Optional[TimeRange]): time range that defines a time slice
          to filter events.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.

    Returns:
      collections.Counter: counter that tracks the number of unique events
          read from storage.
    """
    self._status = definitions.PROCESSING_STATUS_EXPORTING

    time_slice_buffer = None
    if time_slice:
      if time_slice.event_timestamp is not None:
        time_slice = storage_time_range.TimeRange(
            time_slice.start_timestamp, time_slice.end_timestamp)

      if use_time_slicer:
        time_slice_buffer = bufferlib.CircularBuffer(time_slice.duration)

    filter_limit = getattr(event_filter, u'limit', None)
    forward_entries = 0

    number_of_filtered_events = 0
    number_of_events_from_time_slice = 0

    for event in storage_reader.GetSortedEvents(time_range=time_slice):
      if event_filter:
        filter_match = event_filter.Match(event)
      else:
        filter_match = None

      # pylint: disable=singleton-comparison
      if filter_match == False:
        if not time_slice_buffer:
          number_of_filtered_events += 1

        elif forward_entries == 0:
          time_slice_buffer.Append(event)
          number_of_filtered_events += 1

        elif forward_entries <= time_slice_buffer.size:
          self._ExportEvent(
              output_module, event, deduplicate_events=deduplicate_events)
          self._number_of_consumed_events += 1
          number_of_events_from_time_slice += 1
          forward_entries += 1

        else:
          # We reached the maximum size of the time slice and don't need to
          # include other entries.
          number_of_filtered_events += 1
          forward_entries = 0

      else:
        # pylint: disable=singleton-comparison
        if filter_match == True and time_slice_buffer:
          # Empty the time slice buffer.
          for event_in_buffer in time_slice_buffer.Flush():
            self._ExportEvent(
                output_module, event_in_buffer,
                deduplicate_events=deduplicate_events)
            self._number_of_consumed_events += 1
            number_of_filtered_events += 1
            number_of_events_from_time_slice += 1

          forward_entries = 1

        self._ExportEvent(
            output_module, event, deduplicate_events=deduplicate_events)
        self._number_of_consumed_events += 1

        # pylint: disable=singleton-comparison
        if (filter_match == True and filter_limit and
            filter_limit == self._number_of_consumed_events):
          break

    self._FlushExportBuffer(output_module)

    events_counter = collections.Counter()
    events_counter[u'Events filtered'] = number_of_filtered_events
    events_counter[u'Events from time slice'] = number_of_events_from_time_slice
    events_counter[u'Events processed'] = self._number_of_consumed_events

    if self._number_of_duplicate_events:
      events_counter[u'Duplicate events removed'] = (
          self._number_of_duplicate_events)

    if self._number_of_macb_grouped_events:
      events_counter[u'Events MACB grouped'] = (
          self._number_of_macb_grouped_events)

    if filter_limit:
      events_counter[u'Limited By'] = filter_limit

    return events_counter

  def _FlushExportBuffer(self, output_module, deduplicate_events=True):
    """Flushes buffered events and writes them to the output module.

    Args:
      output_module (OutputModule): output module.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
    """
    last_macb_group_identifier = None
    last_content_identifier = None
    macb_group = []

    generator = self._export_event_heap.PopEvents()

    for macb_group_identifier, content_identifier, event in generator:
      if deduplicate_events and last_content_identifier == content_identifier:
        self._number_of_duplicate_events += 1
        continue

      if macb_group_identifier is None:
        if macb_group:
          output_module.WriteEventMACBGroup(macb_group)
          macb_group = []

        output_module.WriteEvent(event)

      else:
        if (last_macb_group_identifier == macb_group_identifier or
            not macb_group):
          macb_group.append(event)

        else:
          output_module.WriteEventMACBGroup(macb_group)
          macb_group = [event]

        self._number_of_macb_grouped_events += 1

      last_macb_group_identifier = macb_group_identifier
      last_content_identifier = content_identifier

    if macb_group:
      output_module.WriteEventMACBGroup(macb_group)

  def _StartAnalysisProcesses(self, storage_writer, analysis_plugins):
    """Starts the analysis processes.

    Args:
      storage_writer (StorageWriter): storage writer.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
    """
    logging.info(u'Starting analysis plugins.')

    for analysis_plugin in analysis_plugins.values():
      self._analysis_plugins[analysis_plugin.NAME] = analysis_plugin

      process = self._StartWorkerProcess(analysis_plugin.NAME, storage_writer)
      if not process:
        logging.error(u'Unable to create analysis process: {0:s}'.format(
            analysis_plugin.NAME))

    logging.info(u'Analysis plugins running')

  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""
    while self._status_update_active:
      # Make a local copy of the PIDs in case the dict is changed by
      # the main thread.
      for pid in list(self._process_information_per_pid.keys()):
        self._CheckStatusAnalysisProcess(pid)

      used_memory = self._process_information.GetUsedMemory() or 0

      display_name = getattr(self._merge_task, u'identifier', u'')

      self._processing_status.UpdateForemanStatus(
          self._name, self._status, self._pid, used_memory, display_name,
          self._number_of_consumed_sources, self._number_of_produced_sources,
          self._number_of_consumed_events, self._number_of_produced_events,
          self._number_of_consumed_event_tags,
          self._number_of_produced_event_tags,
          self._number_of_consumed_errors, self._number_of_produced_errors,
          self._number_of_consumed_reports, self._number_of_produced_reports)

      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

      time.sleep(self._STATUS_UPDATE_INTERVAL)

  def _StopAnalysisProcesses(self, abort=False):
    """Stops the analysis processes.

    Args:
      abort (bool): True to indicated the stop is issued on abort.
    """
    logging.debug(u'Stopping analysis processes.')
    self._StopMonitoringProcesses()

    # Note that multiprocessing.Queue is very sensitive regarding
    # blocking on either a get or a put. So we try to prevent using
    # any blocking behavior.

    if abort:
      # Signal all the processes to abort.
      self._AbortTerminate()

    if not self._use_zeromq:
      logging.debug(u'Emptying queues.')
      for event_queue in self._event_queues.values():
        event_queue.Empty()

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

    processing_status = process_status.get(u'processing_status', None)

    self._RaiseIfNotMonitored(pid)

    display_name = process_status.get(u'display_name', u'')
    number_of_consumed_errors = process_status.get(
        u'number_of_consumed_errors', None)
    number_of_produced_errors = process_status.get(
        u'number_of_produced_errors', None)

    number_of_consumed_event_tags = process_status.get(
        u'number_of_consumed_event_tags', None)
    number_of_produced_event_tags = process_status.get(
        u'number_of_produced_event_tags', None)

    number_of_consumed_events = process_status.get(
        u'number_of_consumed_events', None)
    number_of_produced_events = process_status.get(
        u'number_of_produced_events', None)

    number_of_consumed_reports = process_status.get(
        u'number_of_consumed_reports', None)
    number_of_produced_reports = process_status.get(
        u'number_of_produced_reports', None)

    number_of_consumed_sources = process_status.get(
        u'number_of_consumed_sources', None)
    number_of_produced_sources = process_status.get(
        u'number_of_produced_sources', None)

    if processing_status != definitions.PROCESSING_STATUS_IDLE:
      last_activity_timestamp = process_status.get(
          u'last_activity_timestamp', 0.0)

      if last_activity_timestamp:
        last_activity_timestamp += self._PROCESS_WORKER_TIMEOUT

        current_timestamp = time.time()
        if current_timestamp > last_activity_timestamp:
          logging.error((
              u'Process {0:s} (PID: {1:d}) has not reported activity within '
              u'the timeout period.').format(process.name, pid))
          processing_status = definitions.PROCESSING_STATUS_NOT_RESPONDING

    self._processing_status.UpdateWorkerStatus(
        process.name, processing_status, pid, used_memory, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_events, number_of_produced_events,
        number_of_consumed_event_tags, number_of_produced_event_tags,
        number_of_consumed_errors, number_of_produced_errors,
        number_of_consumed_reports, number_of_produced_reports)

  def _StartWorkerProcess(self, process_name, storage_writer):
    """Creates, starts, monitors and registers a worker process.

    Args:
      process_name (str): process name.
      storage_writer (StorageWriter): storage writer for a session storage used
          to create task storage.

    Returns:
      MultiProcessWorkerProcess: extraction worker process.
    """
    analysis_plugin = self._analysis_plugins.get(process_name, None)
    if not analysis_plugin:
      logging.error(u'Missing analysis plugin: {0:s}'.format(process_name))
      return

    if self._use_zeromq:
      queue_name = u'{0:s} output event queue'.format(process_name)
      output_event_queue = zeromq_queue.ZeroMQPushBindQueue(
          name=queue_name, timeout_seconds=self._QUEUE_TIMEOUT)
      # Open the queue so it can bind to a random port, and we can get the
      # port number to use in the input queue.
      output_event_queue.Open()

    else:
      output_event_queue = multi_process_queue.MultiProcessingQueue(
          timeout=self._QUEUE_TIMEOUT)

    self._event_queues[process_name] = output_event_queue

    if self._use_zeromq:
      queue_name = u'{0:s} input event queue'.format(process_name)
      input_event_queue = zeromq_queue.ZeroMQPullConnectQueue(
          name=queue_name, delay_open=True, port=output_event_queue.port,
          timeout_seconds=self._QUEUE_TIMEOUT)

    else:
      input_event_queue = output_event_queue

    process = analysis_process.AnalysisProcess(
        input_event_queue, storage_writer, self._knowledge_base,
        analysis_plugin, data_location=self._data_location,
        event_filter_expression=self._event_filter_expression,
        name=process_name)

    process.start()

    logging.info(u'Started analysis plugin: {0:s} (PID: {1:d}).'.format(
        process_name, process.pid))

    try:
      self._StartMonitoringProcess(process)
    except (IOError, KeyError) as exception:
      logging.error((
          u'Unable to monitor analysis plugin: {0:s} (PID: {1:d}) '
          u'with error: {2!s}').format(process_name, process.pid, exception))

      process.terminate()
      return

    self._RegisterProcess(process)
    return process

  def AnalyzeEvents(
      self, knowledge_base_object, storage_writer, data_location,
      analysis_plugins, event_filter=None, event_filter_expression=None,
      status_update_callback=None, worker_memory_limit=None):
    """Analyzes events in a plaso storage.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_writer (StorageWriter): storage writer.
      data_location (str): path to the location that data files should
          be loaded from.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
      event_filter (Optional[FilterObject]): event filter.
      event_filter_expression (Optional[str]): event filter expression.
      status_update_callback (Optional[function]): callback function for status
          updates.
      worker_memory_limit (Optional[int]): maximum amount of memory a worker is
          allowed to consume, where None represents the default memory limit.

    Raises:
      KeyboardInterrupt: if a keyboard interrupt was raised.
    """
    if not analysis_plugins:
      return

    keyboard_interrupt = False

    self._analysis_plugins = {}
    self._data_location = data_location
    self._event_filter_expression = event_filter_expression
    self._knowledge_base = knowledge_base_object
    self._status_update_callback = status_update_callback
    self._worker_memory_limit = (
        worker_memory_limit or definitions.DEFAULT_WORKER_MEMORY_LIMIT)

    # Set up the storage writer before the analysis processes.
    storage_writer.StartTaskStorage()

    self._StartAnalysisProcesses(storage_writer, analysis_plugins)

    # Start the status update thread after open of the storage writer
    # so we don't have to clean up the thread if the open fails.
    self._StartStatusUpdateThread()

    try:
      # Open the storage file after creating the worker processes otherwise
      # the ZIP storage file will remain locked as long as the worker processes
      # are alive.
      storage_writer.Open()
      storage_writer.ReadPreprocessingInformation(knowledge_base_object)
      storage_writer.WriteSessionStart()

      try:
        self._AnalyzeEvents(
            storage_writer, analysis_plugins, event_filter=event_filter)

        self._status = definitions.PROCESSING_STATUS_FINALIZING

      except KeyboardInterrupt:
        keyboard_interrupt = True
        self._abort = True

        self._processing_status.aborted = True
        if self._status_update_callback:
          self._status_update_callback(self._processing_status)

      finally:
        storage_writer.WriteSessionCompletion(aborted=self._abort)

        storage_writer.Close()

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

    try:
      self._StopAnalysisProcesses(abort=self._abort)

    except KeyboardInterrupt:
      keyboard_interrupt = True

      self._AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrectly finalized IPC.
      self._KillProcess(os.getpid())

    # Reset values.
    self._analysis_plugins = {}
    self._data_location = None
    self._event_filter_expression = None
    self._knowledge_base = None
    self._status_update_callback = None
    self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

    if keyboard_interrupt:
      raise KeyboardInterrupt

  def ExportEvents(
      self, knowledge_base_object, storage_reader, output_module,
      deduplicate_events=True, event_filter=None, status_update_callback=None,
      time_slice=None, use_time_slicer=False):
    """Exports events using an output module.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      event_filter (Optional[FilterObject]): event filter.
      status_update_callback (Optional[function]): callback function for status
          updates.
      time_slice (Optional[TimeSlice]): slice of time to output.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.

    Returns:
      collections.Counter: counter that tracks the number of events extracted
          from storage.
    """
    self._status_update_callback = status_update_callback

    storage_reader.ReadPreprocessingInformation(knowledge_base_object)

    output_module.Open()
    output_module.WriteHeader()

    self._StartStatusUpdateThread()

    try:
      events_counter = self._ExportEvents(
          storage_reader, output_module, deduplicate_events=deduplicate_events,
          event_filter=event_filter, time_slice=time_slice,
          use_time_slicer=use_time_slicer)

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

    output_module.WriteFooter()
    output_module.Close()

    # Reset values.
    self._status_update_callback = None

    return events_counter
