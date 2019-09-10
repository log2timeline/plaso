# -*- coding: utf-8 -*-
"""The psort multi-processing engine."""

from __future__ import unicode_literals

import collections
import heapq
import os
import time

from plaso.engine import plaso_queue
from plaso.engine import processing_status
from plaso.engine import zeromq_queue
from plaso.containers import tasks
from plaso.lib import bufferlib
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.multi_processing import analysis_process
from plaso.multi_processing import engine as multi_process_engine
from plaso.multi_processing import logger
from plaso.storage import event_tag_index
from plaso.storage import time_range as storage_time_range


class PsortEventHeap(object):
  """Psort event heap."""

  _IDENTIFIER_EXCLUDED_ATTRIBUTES = frozenset([
      'data_type',
      'display_name',
      'filename',
      'inode',
      'parser',
      'tag',
      'timestamp',
      'timestamp_desc'])

  def __init__(self):
    """Initializes a psort events heap."""
    super(PsortEventHeap, self).__init__()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of events on the heap."""
    return len(self._heap)

  def _GetEventIdentifiers(self, event, event_data):
    """Retrieves different identifiers of the event.

    The event data attributes and values can be represented as a string and used
    for sorting and uniquely identifying events. This function determines
    multiple identifiers:
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
      event_data (EventData): event data.

    Returns:
      tuple: containing:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
    """
    attributes = []

    attribute_string = 'data_type: {0:s}'.format(event_data.data_type)
    attributes.append(attribute_string)

    for attribute_name, attribute_value in sorted(event_data.GetAttributes()):
      if attribute_name in self._IDENTIFIER_EXCLUDED_ATTRIBUTES:
        continue

      if not attribute_value:
        continue

      if attribute_name == 'pathspec':
        attribute_value = attribute_value.comparable

      elif isinstance(attribute_value, dict):
        attribute_value = sorted(attribute_value.items())

      elif isinstance(attribute_value, set):
        attribute_value = sorted(list(attribute_value))

      elif isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = repr(attribute_value)

      try:
        attribute_string = '{0:s}: {1!s}'.format(
            attribute_name, attribute_value)
      except UnicodeDecodeError:
        logger.error('Failed to decode attribute {0:s}'.format(
            attribute_name))
      attributes.append(attribute_string)

    # The 'atime', 'ctime', 'crtime', 'mtime' are included for backwards
    # compatibility with the filestat parser.
    if event.timestamp_desc in (
        'atime', 'ctime', 'crtime', 'mtime',
        definitions.TIME_DESCRIPTION_LAST_ACCESS,
        definitions.TIME_DESCRIPTION_CHANGE,
        definitions.TIME_DESCRIPTION_CREATION,
        definitions.TIME_DESCRIPTION_MODIFICATION):
      macb_group_identifier = ', '.join(attributes)
    else:
      macb_group_identifier = None

    timestamp_desc = event.timestamp_desc
    if timestamp_desc is None:
      logger.warning('Missing timestamp_desc attribute')
      timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    attributes.insert(0, timestamp_desc)
    content_identifier = ', '.join(attributes)

    return macb_group_identifier, content_identifier

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      tuple: containing:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
        EventObject: event.
        EventData: event data.
    """
    try:
      macb_group_identifier, content_identifier, event, event_data = (
          heapq.heappop(self._heap))
      if macb_group_identifier == '':
        macb_group_identifier = None
      return macb_group_identifier, content_identifier, event, event_data

    except IndexError:
      return None

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      tuple: containing:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
        EventObject: event.
        EventData: event data.
    """
    heap_values = self.PopEvent()
    while heap_values:
      yield heap_values
      heap_values = self.PopEvent()

  def PushEvent(self, event, event_data):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
    """
    macb_group_identifier, content_identifier = self._GetEventIdentifiers(
        event, event_data)

    # We can ignore the timestamp here because the psort engine only stores
    # events with the same timestamp in the event heap.
    heap_values = (
        macb_group_identifier or '', content_identifier, event, event_data)
    heapq.heappush(self._heap, heap_values)


class PsortMultiProcessEngine(multi_process_engine.MultiProcessEngine):
  """Psort multi-processing engine."""

  _PROCESS_JOIN_TIMEOUT = 5.0
  _PROCESS_WORKER_TIMEOUT = 15.0 * 60.0

  _QUEUE_TIMEOUT = 10 * 60

  def __init__(self):
    """Initializes a psort multi-processing engine."""
    super(PsortMultiProcessEngine, self).__init__()
    self._analysis_plugins = {}
    self._completed_analysis_processes = set()
    self._data_location = None
    self._event_filter_expression = None
    self._event_queues = {}
    self._event_tag_index = event_tag_index.EventTagIndex()
    self._events_status = processing_status.EventsStatus()
    # The export event heap is used to make sure the events are sorted in
    # a deterministic way.
    self._export_event_heap = PsortEventHeap()
    self._export_event_timestamp = 0
    self._knowledge_base = None
    self._memory_profiler = None
    self._merge_task = None
    self._number_of_consumed_event_tags = 0
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_consumed_warnings = 0
    self._number_of_produced_event_tags = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0
    self._number_of_produced_warnings = 0
    self._processing_configuration = None
    self._processing_profiler = None
    self._serializers_profiler = None
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._status_update_callback = None
    self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

  def _AnalyzeEvents(self, storage_writer, analysis_plugins, event_filter=None):
    """Analyzes events in a plaso storage.

    Args:
      storage_writer (StorageWriter): storage writer.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
      event_filter (Optional[FilterObject]): event filter.

    Returns:
      collections.Counter: counter containing information about the events
          processed and filtered.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    self._status = definitions.STATUS_INDICATOR_RUNNING
    self._number_of_consumed_events = 0
    self._number_of_consumed_reports = 0
    self._number_of_consumed_sources = 0
    self._number_of_consumed_warnings = 0
    self._number_of_produced_events = 0
    self._number_of_produced_reports = 0
    self._number_of_produced_sources = 0
    self._number_of_produced_warnings = 0

    number_of_filtered_events = 0

    logger.debug('Processing events.')

    filter_limit = getattr(event_filter, 'limit', None)

    for event in storage_writer.GetSortedEvents():
      event_data_identifier = event.GetEventDataIdentifier()
      event_data = storage_writer.GetEventDataByIdentifier(
          event_data_identifier)

      event_identifier = event.GetIdentifier()
      event_tag = self._event_tag_index.GetEventTagByIdentifier(
          storage_writer, event_identifier)

      if event_filter:
        filter_match = event_filter.Match(event, event_data, event_tag)
      else:
        filter_match = None

      # pylint: disable=singleton-comparison
      if filter_match == False:
        number_of_filtered_events += 1
        continue

      for event_queue in self._event_queues.values():
        # TODO: Check for premature exit of analysis plugins.
        event_queue.PushItem((event, event_data))

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
    plugin_names = [plugin_name for plugin_name in analysis_plugins.keys()]
    while plugin_names:
      for plugin_name in list(plugin_names):
        if self._abort:
          break

        # TODO: temporary solution.
        task = tasks.Task()
        task.storage_format = definitions.STORAGE_FORMAT_SQLITE
        task.identifier = plugin_name

        merge_ready = storage_writer.CheckTaskReadyForMerge(task)
        if merge_ready:
          storage_writer.PrepareMergeTaskStorage(task)
          self._status = definitions.STATUS_INDICATOR_MERGING

          event_queue = self._event_queues[plugin_name]
          del self._event_queues[plugin_name]

          event_queue.Close()

          storage_merge_reader = storage_writer.StartMergeTaskStorage(task)

          storage_merge_reader.MergeAttributeContainers(
              callback=self._MergeEventTag)
          # TODO: temporary solution.
          plugin_names.remove(plugin_name)

          self._status = definitions.STATUS_INDICATOR_RUNNING

          self._number_of_produced_event_tags = (
              storage_writer.number_of_event_tags)
          self._number_of_produced_reports = (
              storage_writer.number_of_analysis_reports)

    try:
      storage_writer.StopTaskStorage(abort=self._abort)
    except (IOError, OSError) as exception:
      logger.error('Unable to stop task storage with error: {0!s}'.format(
          exception))

    if self._abort:
      logger.debug('Processing aborted.')
    else:
      logger.debug('Processing completed.')

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

  def _ExportEvent(
      self, storage_reader, output_module, event, event_data,
      deduplicate_events=True):
    """Exports an event using an output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      event (EventObject): event.
      event_data (EventData): event data.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
    """
    if event.timestamp != self._export_event_timestamp:
      self._FlushExportBuffer(
          storage_reader, output_module,
          deduplicate_events=deduplicate_events)
      self._export_event_timestamp = event.timestamp

    self._export_event_heap.PushEvent(event, event_data)

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
    """
    self._status = definitions.STATUS_INDICATOR_EXPORTING

    time_slice_buffer = None
    time_slice_range = None

    if time_slice:
      if time_slice.event_timestamp is not None:
        time_slice_range = storage_time_range.TimeRange(
            time_slice.start_timestamp, time_slice.end_timestamp)

      if use_time_slicer:
        time_slice_buffer = bufferlib.CircularBuffer(time_slice.duration)

    filter_limit = getattr(event_filter, 'limit', None)
    forward_entries = 0

    self._events_status.number_of_filtered_events = 0
    self._events_status.number_of_events_from_time_slice = 0

    for event in storage_reader.GetSortedEvents(time_range=time_slice_range):
      event_data_identifier = event.GetEventDataIdentifier()
      event_data = storage_reader.GetEventDataByIdentifier(
          event_data_identifier)

      event_identifier = event.GetIdentifier()
      event_tag = self._event_tag_index.GetEventTagByIdentifier(
          storage_reader, event_identifier)

      if time_slice_range and event.timestamp != time_slice.event_timestamp:
        self._events_status.number_of_events_from_time_slice += 1

      if event_filter:
        filter_match = event_filter.Match(event, event_data, event_tag)
      else:
        filter_match = None

      # pylint: disable=singleton-comparison
      if filter_match == False:
        if not time_slice_buffer:
          self._events_status.number_of_filtered_events += 1

        elif forward_entries == 0:
          time_slice_buffer.Append((event, event_data))
          self._events_status.number_of_filtered_events += 1

        elif forward_entries <= time_slice_buffer.size:
          self._ExportEvent(
              storage_reader, output_module, event, event_data,
              deduplicate_events=deduplicate_events)
          self._number_of_consumed_events += 1
          self._events_status.number_of_events_from_time_slice += 1
          forward_entries += 1

        else:
          # We reached the maximum size of the time slice and don't need to
          # include other entries.
          self._events_status.number_of_filtered_events += 1
          forward_entries = 0

      else:
        # pylint: disable=singleton-comparison
        if filter_match == True and time_slice_buffer:
          # Empty the time slice buffer.
          for event_in_buffer, event_data_in_buffer in (
              time_slice_buffer.Flush()):
            self._ExportEvent(
                storage_reader, output_module, event_in_buffer,
                event_data_in_buffer, deduplicate_events=deduplicate_events)
            self._number_of_consumed_events += 1
            self._events_status.number_of_filtered_events += 1
            self._events_status.number_of_events_from_time_slice += 1

          forward_entries = 1

        self._ExportEvent(
            storage_reader, output_module, event, event_data,
            deduplicate_events=deduplicate_events)
        self._number_of_consumed_events += 1

        # pylint: disable=singleton-comparison
        if (filter_match == True and filter_limit and
            filter_limit == self._number_of_consumed_events):
          break

    self._FlushExportBuffer(storage_reader, output_module)

  def _FlushExportBuffer(
      self, storage_reader, output_module, deduplicate_events=True):
    """Flushes buffered events and writes them to the output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
    """
    last_macb_group_identifier = None
    last_content_identifier = None
    macb_group = []

    generator = self._export_event_heap.PopEvents()

    for macb_group_identifier, content_identifier, event, event_data in (
        generator):
      if deduplicate_events and last_content_identifier == content_identifier:
        self._events_status.number_of_duplicate_events += 1
        continue

      event_identifier = event.GetIdentifier()
      event_tag = self._event_tag_index.GetEventTagByIdentifier(
          storage_reader, event_identifier)

      if macb_group_identifier is None:
        if macb_group:
          output_module.WriteEventMACBGroup(macb_group)
          macb_group = []

        output_module.WriteEvent(event, event_data, event_tag)

      else:
        if (last_macb_group_identifier == macb_group_identifier or
            not macb_group):
          macb_group.append((event, event_data, event_tag))

        else:
          output_module.WriteEventMACBGroup(macb_group)
          macb_group = [(event, event_data, event_tag)]

        self._events_status.number_of_macb_grouped_events += 1

      last_macb_group_identifier = macb_group_identifier
      last_content_identifier = content_identifier

    if macb_group:
      output_module.WriteEventMACBGroup(macb_group)

  def _MergeEventTag(self, storage_writer, attribute_container):
    """Merges an event tag with the last stored event tag.

    If there is an existing event the provided event tag is updated with
    the contents of the existing one. After which the event tag index is
    updated.

    Args:
      storage_writer (StorageWriter): storage writer.
      attribute_container (AttributeContainer): container.
    """
    if attribute_container.CONTAINER_TYPE != 'event_tag':
      return

    event_identifier = attribute_container.GetEventIdentifier()
    if not event_identifier:
      return

    # Check if the event has already been tagged on a previous occasion,
    # we need to append the event tag to the last stored one.
    stored_event_tag = self._event_tag_index.GetEventTagByIdentifier(
        storage_writer, event_identifier)
    if stored_event_tag:
      attribute_container.AddComment(stored_event_tag.comment)
      attribute_container.AddLabels(stored_event_tag.labels)

    self._event_tag_index.SetEventTag(attribute_container)

  def _StartAnalysisProcesses(self, storage_writer, analysis_plugins):
    """Starts the analysis processes.

    Args:
      storage_writer (StorageWriter): storage writer.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
    """
    logger.info('Starting analysis plugins.')

    for analysis_plugin in analysis_plugins.values():
      self._analysis_plugins[analysis_plugin.NAME] = analysis_plugin

      process = self._StartWorkerProcess(analysis_plugin.NAME, storage_writer)
      if not process:
        logger.error('Unable to create analysis process: {0:s}'.format(
            analysis_plugin.NAME))

    logger.info('Analysis plugins running')

  def _StatusUpdateThreadMain(self):
    """Main function of the status update thread."""
    while self._status_update_active:
      # Make a local copy of the PIDs in case the dict is changed by
      # the main thread.
      for pid in list(self._process_information_per_pid.keys()):
        self._CheckStatusAnalysisProcess(pid)

      self._UpdateForemanProcessStatus()

      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

      time.sleep(self._STATUS_UPDATE_INTERVAL)

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
        self._number_of_consumed_warnings, self._number_of_produced_warnings,
        self._number_of_consumed_reports, self._number_of_produced_reports)

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

    number_of_consumed_warnings = process_status.get(
        'number_of_consumed_warnings', None)
    number_of_produced_warnings = process_status.get(
        'number_of_produced_warnings', None)

    if status_indicator != definitions.STATUS_INDICATOR_IDLE:
      last_activity_timestamp = process_status.get(
          'last_activity_timestamp', 0.0)

      if last_activity_timestamp:
        last_activity_timestamp += self._PROCESS_WORKER_TIMEOUT

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
        number_of_consumed_warnings, number_of_produced_warnings)

  def _StartWorkerProcess(self, process_name, storage_writer):
    """Creates, starts, monitors and registers a worker process.

    Args:
      process_name (str): process name.
      storage_writer (StorageWriter): storage writer for a session storage used
          to create task storage.

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
        input_event_queue, storage_writer, self._knowledge_base,
        analysis_plugin, self._processing_configuration,
        data_location=self._data_location,
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

  def AnalyzeEvents(
      self, knowledge_base_object, storage_writer, data_location,
      analysis_plugins, processing_configuration, event_filter=None,
      event_filter_expression=None, status_update_callback=None,
      worker_memory_limit=None):
    """Analyzes events in a plaso storage.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_writer (StorageWriter): storage writer.
      data_location (str): path to the location that data files should
          be loaded from.
      analysis_plugins (dict[str, AnalysisPlugin]): analysis plugins that
          should be run and their names.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      event_filter (Optional[FilterObject]): event filter.
      event_filter_expression (Optional[str]): event filter expression.
      status_update_callback (Optional[function]): callback function for status
          updates.
      worker_memory_limit (Optional[int]): maximum amount of memory a worker is
          allowed to consume, where None represents the default memory limit
          and 0 represents no limit.

    Raises:
      KeyboardInterrupt: if a keyboard interrupt was raised.
    """
    if not analysis_plugins:
      return

    keyboard_interrupt = False

    self._analysis_plugins = {}
    self._data_location = data_location
    self._event_filter_expression = event_filter_expression
    self._events_status = processing_status.EventsStatus()
    self._knowledge_base = knowledge_base_object
    self._status_update_callback = status_update_callback
    self._processing_configuration = processing_configuration

    if worker_memory_limit is None:
      self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT
    else:
      self._worker_memory_limit = worker_memory_limit

    self._StartProfiling(self._processing_configuration.profiling)

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

        self._status = definitions.STATUS_INDICATOR_FINALIZING

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

    self._StopProfiling()

    # Reset values.
    self._analysis_plugins = {}
    self._data_location = None
    self._event_filter_expression = None
    self._knowledge_base = None
    self._processing_configuration = None
    self._status_update_callback = None
    self._worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

    if keyboard_interrupt:
      raise KeyboardInterrupt

    if keyboard_interrupt:
      raise KeyboardInterrupt

  def ExportEvents(
      self, knowledge_base_object, storage_reader, output_module,
      processing_configuration, deduplicate_events=True, event_filter=None,
      status_update_callback=None, time_slice=None, use_time_slicer=False):
    """Exports events using an output module.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      event_filter (Optional[FilterObject]): event filter.
      status_update_callback (Optional[function]): callback function for status
          updates.
      time_slice (Optional[TimeSlice]): slice of time to output.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.
    """
    self._events_status = processing_status.EventsStatus()
    self._processing_configuration = processing_configuration
    self._status_update_callback = status_update_callback

    storage_reader.ReadPreprocessingInformation(knowledge_base_object)

    total_number_of_events = 0
    for session in storage_reader.GetSessions():
      total_number_of_events += session.parsers_counter['total']

    self._events_status.total_number_of_events = total_number_of_events

    output_module.Open()
    output_module.WriteHeader()

    self._StartStatusUpdateThread()

    self._StartProfiling(self._processing_configuration.profiling)

    try:
      self._ExportEvents(
          storage_reader, output_module, deduplicate_events=deduplicate_events,
          event_filter=event_filter, time_slice=time_slice,
          use_time_slicer=use_time_slicer)

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

    output_module.WriteFooter()
    output_module.Close()

    self._StopProfiling()

    self._UpdateForemanProcessStatus()

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

    # Reset values.
    self._status_update_callback = None
    self._processing_configuration = None
    self._events_status = None
