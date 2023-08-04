# -*- coding: utf-8 -*-
"""The task-based multi-process processing extraction engine."""

import collections
import heapq
import logging
import multiprocessing
import os
import re
import time
import traceback

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import counts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import warnings
from plaso.engine import extractors
from plaso.engine import path_helper
from plaso.engine import timeliner
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import loggers
from plaso.multi_process import extraction_process
from plaso.multi_process import logger
from plaso.multi_process import merge_helpers
from plaso.multi_process import plaso_queue
from plaso.multi_process import task_engine
from plaso.multi_process import task_manager
from plaso.multi_process import zeromq_queue


class _EventSourceHeap(object):
  """Class that defines an event source heap."""

  def __init__(self, maximum_number_of_items=50000):
    """Initializes an event source heap.

    Args:
      maximum_number_of_items (Optional[int]): maximum number of items
          in the heap.
    """
    super(_EventSourceHeap, self).__init__()
    self._heap = []
    self._maximum_number_of_items = maximum_number_of_items

  def IsFull(self):
    """Determines if the heap is full.

    Returns:
      bool: True if the heap is full, False otherwise.
    """
    return len(self._heap) >= self._maximum_number_of_items

  def PopEventSource(self):
    """Pops an event source from the heap.

    Returns:
      EventSource: an event source or None on if no event source is available.
    """
    try:
      _, _, event_source = heapq.heappop(self._heap)

    except IndexError:
      return None

    return event_source

  def PushEventSource(self, event_source):
    """Pushes an event source onto the heap.

    Args:
      event_source (EventSource): event source.
    """
    if event_source.file_entry_type == (
        dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY):
      weight = 1
    else:
      weight = 100

    heap_values = (weight, time.time(), event_source)
    heapq.heappush(self._heap, heap_values)


class ExtractionMultiProcessEngine(task_engine.TaskMultiProcessEngine):
  """Task-based multi-process extraction engine.

  This class contains functionality to:
  * monitor and manage extraction tasks;
  * merge results returned by extraction worker processes.
  """

  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_YEAR_LESS_LOG_HELPER = events.YearLessLogHelper.CONTAINER_TYPE

  # Maximum number of dfVFS file system objects to cache in the foreman process.
  _FILE_SYSTEM_CACHE_SIZE = 3

  # Maximum number of concurrent tasks.
  _MAXIMUM_NUMBER_OF_TASKS = 10000

  _TASK_QUEUE_TIMEOUT_SECONDS = 2

  _UNICODE_SURROGATES_RE = re.compile('[\ud800-\udfff]')

  _WORKER_PROCESSES_MINIMUM = 2
  _WORKER_PROCESSES_MAXIMUM = 99

  _ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS = 10 * 60

  def __init__(
      self, maximum_number_of_tasks=None, number_of_worker_processes=0,
      status_update_callback=None, worker_memory_limit=None,
      worker_timeout=None):
    """Initializes an engine.

    Args:
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
      number_of_worker_processes (Optional[int]): number of worker processes.
      status_update_callback (Optional[function]): callback function for status
          updates.
      worker_memory_limit (Optional[int]): maximum amount of memory a worker is
          allowed to consume, where None represents the default memory limit
          and 0 represents no limit.
      worker_timeout (Optional[float]): number of minutes before a worker
          process that is not providing status updates is considered inactive,
          where None or 0.0 represents the default timeout.
    """
    if maximum_number_of_tasks is None:
      maximum_number_of_tasks = self._MAXIMUM_NUMBER_OF_TASKS

    if number_of_worker_processes < 1:
      # One worker for each "available" CPU (minus other processes).
      # The number here is derived from the fact that the engine starts up:
      # * A main process.
      #
      # If we want to utilize all CPUs on the system we therefore need to start
      # up workers that amounts to the total number of CPUs - the other
      # processes.
      try:
        cpu_count = multiprocessing.cpu_count() - 1

        if cpu_count <= self._WORKER_PROCESSES_MINIMUM:
          cpu_count = self._WORKER_PROCESSES_MINIMUM

        elif cpu_count >= self._WORKER_PROCESSES_MAXIMUM:
          cpu_count = self._WORKER_PROCESSES_MAXIMUM

      except NotImplementedError:
        logger.error((
            'Unable to determine number of CPUs defaulting to {0:d} worker '
            'processes.').format(self._WORKER_PROCESSES_MINIMUM))
        cpu_count = self._WORKER_PROCESSES_MINIMUM

      number_of_worker_processes = cpu_count

    if worker_memory_limit is None:
      worker_memory_limit = definitions.DEFAULT_WORKER_MEMORY_LIMIT

    if not worker_timeout:
      worker_timeout = definitions.DEFAULT_WORKER_TIMEOUT

    super(ExtractionMultiProcessEngine, self).__init__()
    self._enable_sigsegv_handler = False
    self._event_data_timeliner = None
    self._extraction_worker = None
    self._file_system_cache = []
    self._maximum_number_of_containers = 50
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._merge_task = None
    self._merge_task_on_hold = None
    self._number_of_consumed_event_data = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_event_data = 0
    self._number_of_produced_events = 0
    self._number_of_produced_sources = 0
    self._number_of_worker_processes = number_of_worker_processes
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._resolver_context = context.Context()
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._status_update_callback = status_update_callback
    self._task_manager = task_manager.TaskManager()
    self._task_merge_helper = None
    self._task_merge_helper_on_hold = None
    self._task_queue = None
    self._task_queue_port = None
    self._task_storage_format = None
    self._worker_memory_limit = worker_memory_limit
    self._worker_timeout = worker_timeout
    self._system_configurations = None

  def _CacheFileSystem(self, file_system):
    """Caches a dfVFS file system object.

    Keeping and additional reference to a dfVFS file system object causes the
    object to remain cached in the resolver context. This minimizes the number
    times the file system is re-opened.

    Args:
      file_system (dfvfs.FileSystem): file system.
    """
    if file_system not in self._file_system_cache:
      if len(self._file_system_cache) == self._FILE_SYSTEM_CACHE_SIZE:
        self._file_system_cache.pop(0)
      self._file_system_cache.append(file_system)

    elif len(self._file_system_cache) == self._FILE_SYSTEM_CACHE_SIZE:
      # Move the file system to the end of the list to preserve the most
      # recently file system object.
      self._file_system_cache.remove(file_system)
      self._file_system_cache.append(file_system)

  def _CheckExcludedPathSpec(self, file_system, path_spec):
    """Determines if the path specification should be excluded from extraction.

    Args:
      file_system (dfvfs.FileSystem): file system which the path specification
          is part of.
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      bool: True if the path specification should be excluded from extraction.
    """
    for find_spec in self._excluded_file_system_find_specs or []:
      if find_spec.ComparePathSpecLocation(path_spec, file_system):
        return True

    return False

  def _CollectInitialEventSources(self, storage_writer, file_system_path_specs):
    """Collects the initial event sources.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.
    """
    self._status = definitions.STATUS_INDICATOR_COLLECTING

    included_find_specs = self.GetCollectionIncludedFindSpecs()

    for file_system_path_spec in file_system_path_specs:
      if self._abort:
        break

      file_system = path_spec_resolver.Resolver.OpenFileSystem(
          file_system_path_spec, resolver_context=self._resolver_context)

      path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
          file_system_path_spec, find_specs=included_find_specs,
          recurse_file_system=False, resolver_context=self._resolver_context)
      for path_spec in path_spec_generator:
        if self._abort:
          break

        if self._CheckExcludedPathSpec(file_system, path_spec):
          display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
              path_spec)
          logger.debug('Excluded from extraction: {0:s}.'.format(display_name))
          continue

        # TODO: determine if event sources should be DataStream or FileEntry
        # or both.
        event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
        storage_writer.AddAttributeContainer(event_source)

        self._number_of_produced_sources += 1

        # Update the foreman process status in case we are using a filter file.
        self._UpdateForemanProcessStatus()

        if self._status_update_callback:
          self._status_update_callback(self._processing_status)

  def _CreateTask(self, storage_writer, session_identifier, event_source):
    """Creates a task to processes an event source.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      session_identifier (str): the identifier of the session the tasks are
          part of.
      event_source (EventSource): event source.

    Returns:
      Task: task or None if no task could be created.
    """
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        event_source.path_spec, resolver_context=self._resolver_context)
    if file_entry is None:
      self._ProduceExtractionWarning(
          storage_writer, 'Unable to open file entry', event_source.path_spec)
      return None

    file_system = file_entry.GetFileSystem()

    if not event_source.path_spec.IsSystemLevel():
      self._CacheFileSystem(file_system)

    if self._CheckExcludedPathSpec(file_system, event_source.path_spec):
      display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
          event_source.path_spec)
      logger.debug('Excluded from extraction: {0:s}.'.format(
          display_name))
      return None

    task = self._task_manager.CreateTask(
        session_identifier, storage_format=self._task_storage_format)
    task.file_entry_type = event_source.file_entry_type
    task.path_spec = event_source.path_spec

    return task

  def _FillEventSourceHeap(
      self, storage_writer, event_source_heap, start_with_first=False):
    """Fills the event source heap with the available written event sources.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      event_source_heap (_EventSourceHeap): event source heap.
      start_with_first (Optional[bool]): True if the function should start
          with the first written event source.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('fill_event_source_heap')

    if self._processing_profiler:
      self._processing_profiler.StartTiming('get_event_source')

    if start_with_first:
      event_source = storage_writer.GetFirstWrittenEventSource()
    else:
      event_source = storage_writer.GetNextWrittenEventSource()

    if self._processing_profiler:
      self._processing_profiler.StopTiming('get_event_source')

    while event_source:
      event_source_heap.PushEventSource(event_source)
      if event_source_heap.IsFull():
        logger.debug('Event source heap is full.')
        break

      if self._processing_profiler:
        self._processing_profiler.StartTiming('get_event_source')

      event_source = storage_writer.GetNextWrittenEventSource()

      if self._processing_profiler:
        self._processing_profiler.StopTiming('get_event_source')

    if self._processing_profiler:
      self._processing_profiler.StopTiming('fill_event_source_heap')

  def _GetPathSpecificationString(self, path_spec):
    """Retrieves a printable string representation of the path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: printable string representation of the path specification.
    """
    path_spec_string = path_spec.comparable

    if self._UNICODE_SURROGATES_RE.search(path_spec_string):
      path_spec_string = path_spec_string.encode(
          'utf-8', errors='surrogateescape')
      path_spec_string = path_spec_string.decode(
          'utf-8', errors='backslashreplace')

    return path_spec_string

  def _MergeAttributeContainer(self, storage_writer, merge_helper, container):
    """Merges an attribute container from a task store into the storage writer.

    Args:
      storage_writer (StorageWriter): storage writer.
      merge_helper (ExtractionTaskMergeHelper): helper to merge attribute
          containers.
      container (AttributeContainer): attribute container.
    """
    self._status = definitions.STATUS_INDICATOR_MERGING

    if container.CONTAINER_TYPE in (
        self._CONTAINER_TYPE_EVENT_DATA,
        self._CONTAINER_TYPE_YEAR_LESS_LOG_HELPER):
      event_data_stream_identifier = container.GetEventDataStreamIdentifier()
      event_data_stream_lookup_key = None
      if event_data_stream_identifier:
        event_data_stream_lookup_key = (
            event_data_stream_identifier.CopyToString())

        event_data_stream_identifier = (
            merge_helper.GetAttributeContainerIdentifier(
                event_data_stream_lookup_key))

      if event_data_stream_identifier:
        container.SetEventDataStreamIdentifier(event_data_stream_identifier)
      elif event_data_stream_lookup_key:
        identifier = container.GetIdentifier()
        identifier_string = identifier.CopyToString()

        # TODO: store this as a merge warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge {0:s} attribute container: {1:s} since '
            'corresponding event data stream: {2:s} could not be '
            'found.').format(
                container.CONTAINER_TYPE, identifier_string,
                event_data_stream_lookup_key))
        return

    elif container.CONTAINER_TYPE in (
        'windows_eventlog_message_string', 'windows_wevt_template_event'):
      message_file_identifier = container.GetMessageFileIdentifier()
      message_file_lookup_key = message_file_identifier.CopyToString()

      message_file_identifier = merge_helper.GetAttributeContainerIdentifier(
          message_file_lookup_key)

      if message_file_identifier:
        container.SetMessageFileIdentifier(message_file_identifier)
      else:
        identifier = container.GetIdentifier()
        identifier_string = identifier.CopyToString()

        # TODO: store this as a merge warning so this is preserved
        # in the storage file.
        if container.CONTAINER_TYPE == 'windows_eventlog_message_string':
          description = 'Windows EventLog message string'
        else:
          description = 'WEVT_TEMPLATE event definition'

        logger.error((
            'Unable to merge {0:s} attribute container: {1:s} since '
            'corresponding Windows EventLog message file: {2:s} could not '
            'be found.').format(
                description, identifier_string, message_file_lookup_key))
        return

    lookup_key = None
    if container.CONTAINER_TYPE in (
        self._CONTAINER_TYPE_EVENT_DATA,
        self._CONTAINER_TYPE_EVENT_DATA_STREAM,
        'windows_eventlog_message_file'):
      # Preserve the lookup key before adding it to the attribute container
      # store.
      identifier = container.GetIdentifier()
      lookup_key = identifier.CopyToString()

    storage_writer.AddAttributeContainer(container)

    if lookup_key:
      identifier = container.GetIdentifier()
      merge_helper.SetAttributeContainerIdentifier(lookup_key, identifier)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      self._number_of_produced_event_data += 1

      self._status = definitions.STATUS_INDICATOR_TIMELINING

      event_data_stream_identifier = container.GetEventDataStreamIdentifier()

      event_data_stream = None
      if event_data_stream_identifier:
        event_data_stream = (
            self._storage_writer.GetAttributeContainerByIdentifier(
                self._CONTAINER_TYPE_EVENT_DATA_STREAM,
                event_data_stream_identifier))

      # Generate events on merge.
      self._event_data_timeliner.ProcessEventData(
          storage_writer, container, event_data_stream)

      self._number_of_consumed_event_data += 1
      self._number_of_produced_events += (
          self._event_data_timeliner.number_of_produced_events)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_SOURCE:
      self._number_of_produced_sources += 1

    self._status = definitions.STATUS_INDICATOR_RUNNING

  def _MergeAttributeContainers(
        self, storage_writer, merge_helper, maximum_number_of_containers=0):
    """Merges attribute containers from a task store into the storage writer.

    Args:
      storage_writer (StorageWriter): storage writer.
      merge_helper (ExtractionTaskMergeHelper): helper to merge attribute
          containers.
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      int: number of containers merged.
    """
    number_of_containers = 0

    container = merge_helper.GetAttributeContainer()

    while container:
      number_of_containers += 1

      self._MergeAttributeContainer(storage_writer, merge_helper, container)

      if 0 < maximum_number_of_containers <= number_of_containers:
        break

      container = merge_helper.GetAttributeContainer()

    return number_of_containers

  def _MergeTaskStorage(self, storage_writer, session_identifier):
    """Merges a task storage with the session storage.

    This function checks all task stores that are ready to merge and updates
    the scheduled tasks. Note that to prevent this function holding up
    the task scheduling loop only the first available task storage is merged.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage used
          to merge task storage.
      session_identifier (str): the identifier of the session the tasks are
          part of.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('merge_check')

    task_identifiers = self._GetProcessedTaskIdentifiers(
        self._task_storage_format, session_identifier)

    for task_identifier in task_identifiers:
      try:
        task = self._task_manager.GetProcessedTaskByIdentifier(task_identifier)

        self._task_manager.SampleTaskStatus(task, 'processed')

        to_merge = self._task_manager.CheckTaskToMerge(task)
        if not to_merge:
          self._RemoveProcessedTaskStorage(self._task_storage_format, task)

          self._task_manager.RemoveTask(task)
          self._task_manager.SampleTaskStatus(task, 'removed_processed')

        else:
          self._PrepareMergeTaskStorage(self._task_storage_format, task)
          self._task_manager.UpdateTaskAsPendingMerge(task)

      except KeyError as exception:
        logger.error(
            'Unable to retrieve task: {0:s} to prepare it to be merged '
            'with error: {1!s}.'.format(task_identifier, exception))
        continue

    if self._processing_profiler:
      self._processing_profiler.StopTiming('merge_check')

    task = None
    if not self._task_merge_helper_on_hold:
      task = self._task_manager.GetTaskPendingMerge(self._merge_task)

    if task or self._task_merge_helper:
      if self._processing_profiler:
        self._processing_profiler.StartTiming('merge')

      if task:
        if self._task_merge_helper:
          self._merge_task_on_hold = self._merge_task
          self._task_merge_helper_on_hold = self._task_merge_helper

          self._task_manager.SampleTaskStatus(
              self._merge_task_on_hold, 'merge_on_hold')

        self._merge_task = task
        try:
          task_storage_reader = self._GetMergeTaskStorage(
              self._task_storage_format, task)

          self._task_merge_helper = merge_helpers.ExtractionTaskMergeHelper(
              task_storage_reader, task.identifier)

          self._task_manager.SampleTaskStatus(task, 'merge_started')

        except IOError as exception:
          logger.error((
              'Unable to merge results of task: {0:s} '
              'with error: {1!s}').format(task.identifier, exception))
          self._task_merge_helper = None

      if self._task_merge_helper:
        merge_duration = time.time()

        number_of_containers = self._MergeAttributeContainers(
            storage_writer, self._task_merge_helper,
            maximum_number_of_containers=self._maximum_number_of_containers)

        merge_duration = time.time() - merge_duration

        fully_merged = self._task_merge_helper.fully_merged

        if merge_duration > 0.0 and number_of_containers > 0:
          # Limit the number of attribute containers from a single task-based
          # storage file that are merged per loop to keep tasks flowing.
          containers_per_second = number_of_containers / merge_duration
          maximum_number_of_containers = int(0.5 * containers_per_second)

          if fully_merged:
            self._maximum_number_of_containers = max(
                self._maximum_number_of_containers,
                maximum_number_of_containers)

          else:
            self._maximum_number_of_containers = maximum_number_of_containers

      else:
        # TODO: Do something more sensible when this happens, perhaps
        # retrying the task once that is implemented. For now, we mark the task
        # as fully merged because we can't continue with it.
        fully_merged = True

      if self._processing_profiler:
        self._processing_profiler.StopTiming('merge')

      if fully_merged:
        self._task_merge_helper.Close()

        self._RemoveMergeTaskStorage(
            self._task_storage_format, self._merge_task)

        try:
          self._task_manager.CompleteTask(self._merge_task)

        except KeyError as exception:
          logger.error(
              'Unable to complete task: {0:s} with error: {1!s}'.format(
                  self._merge_task.identifier, exception))

        if not self._task_merge_helper_on_hold:
          self._merge_task = None
          self._task_merge_helper = None
        else:
          self._merge_task = self._merge_task_on_hold
          self._task_merge_helper = self._task_merge_helper_on_hold

          self._merge_task_on_hold = None
          self._task_merge_helper_on_hold = None

          self._task_manager.SampleTaskStatus(self._merge_task, 'merge_resumed')

  def _ProduceExtractionWarning(self, storage_writer, message, path_spec):
    """Produces an extraction warning.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      message (str): message of the warning.
      path_spec (dfvfs.PathSpec): path specification.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    warning = warnings.ExtractionWarning(message=message, path_spec=path_spec)
    storage_writer.AddAttributeContainer(warning)

    if path_spec:
      self._processing_status.error_path_specs.append(path_spec)

  def _ProcessEventSources(self, storage_writer, session_identifier):
    """Processes event sources.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      session_identifier (str): the identifier of the session the tasks are
          part of.
    """
    logger.debug('Task scheduler started')

    self._status = definitions.STATUS_INDICATOR_RUNNING

    # TODO: make tasks persistent.

    # TODO: protect task scheduler loop by catch all and
    # handle abort path.

    event_source_heap = _EventSourceHeap()

    self._FillEventSourceHeap(
        storage_writer, event_source_heap, start_with_first=True)

    event_source = event_source_heap.PopEventSource()

    task = None
    has_pending_tasks = True

    while event_source or has_pending_tasks:
      if self._abort:
        break

      try:
        if not task:
          task = self._task_manager.CreateRetryTask()

        if not task and event_source:
          task = self._CreateTask(
              storage_writer, session_identifier, event_source)

          event_source = None

          self._number_of_consumed_sources += 1

        if task:
          if not self._ScheduleTask(task):
            self._task_manager.SampleTaskStatus(task, 'schedule_attempted')

          else:
            path_spec_string = self._GetPathSpecificationString(task.path_spec)
            logger.debug(
                'Scheduled task: {0:s} for path specification: {1:s}'.format(
                    task.identifier, path_spec_string.replace('\n', ' ')))

            self._task_manager.SampleTaskStatus(task, 'scheduled')

            task = None

        self._MergeTaskStorage(storage_writer, session_identifier)

        if event_source_heap.IsFull():
          logger.debug('Event source heap is full.')
        else:
          self._FillEventSourceHeap(storage_writer, event_source_heap)

        if not task and not event_source:
          event_source = event_source_heap.PopEventSource()

        has_pending_tasks = self._task_manager.HasPendingTasks()

      except KeyboardInterrupt:
        if self._debug_output:
          traceback.print_exc()
        self._abort = True

        self._processing_status.aborted = True
        if self._status_update_callback:
          self._status_update_callback(self._processing_status)

      # All exceptions need to be caught here to prevent the foreman
      # from being killed by an uncaught exception.
      except Exception as exception:  # pylint: disable=broad-except
        self._ProduceExtractionWarning(storage_writer, (
            'unable to process path specification with error: '
            '{0!s}').format(exception), event_source.path_spec)
        event_source = None

    for task in self._task_manager.GetFailedTasks():
      self._ProduceExtractionWarning(
          storage_writer, 'Worker failed to process path specification',
          task.path_spec)

    self._status = definitions.STATUS_INDICATOR_IDLE

    if self._abort:
      logger.debug('Task scheduler aborted')
    else:
      logger.debug('Task scheduler stopped')

  def _ProcessSource(
      self, storage_writer, session_identifier, file_system_path_specs):
    """Processes file systems within a source.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      session_identifier (str): the identifier of the session the tasks are
          part of.
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('process_source')

    self._number_of_consumed_event_data = 0
    self._number_of_consumed_sources = 0
    self._number_of_produced_event_data = 0
    self._number_of_produced_events = 0
    self._number_of_produced_sources = 0

    stored_parsers_counter = collections.Counter({
        parser_count.name: parser_count
        for parser_count in storage_writer.GetAttributeContainers(
            'parser_count')})

    self._CollectInitialEventSources(storage_writer, file_system_path_specs)

    self._ProcessEventSources(storage_writer, session_identifier)

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    for key, value in self._event_data_timeliner.parsers_counter.items():
      parser_count = stored_parsers_counter.get(key, None)
      if parser_count:
        parser_count.number_of_events += value
        storage_writer.UpdateAttributeContainer(parser_count)
      else:
        parser_count = counts.ParserCount(name=key, number_of_events=value)
        storage_writer.AddAttributeContainer(parser_count)

    if self._processing_profiler:
      self._processing_profiler.StopTiming('process_source')

    # Update the foreman process and task status in case we are using
    # a filter file.
    self._UpdateForemanProcessStatus()

    tasks_status = self._task_manager.GetStatusInformation()
    if self._task_queue_profiler:
      self._task_queue_profiler.Sample(tasks_status)

    self._processing_status.UpdateTasksStatus(tasks_status)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def _ScheduleTask(self, task):
    """Schedules a task.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task was scheduled.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('schedule_task')

    try:
      self._task_queue.PushItem(task, block=False)
      is_scheduled = True

    except errors.QueueFull:
      is_scheduled = False

    if self._processing_profiler:
      self._processing_profiler.StopTiming('schedule_task')

    return is_scheduled

  def _StartWorkerProcess(self, process_name):
    """Creates, starts, monitors and registers a worker process.

    Args:
      process_name (str): process name.

    Returns:
      MultiProcessWorkerProcess: extraction worker process or None if the
          process could not be started.
    """
    logger.debug('Starting worker process {0:s}'.format(process_name))

    queue_name = '{0:s} task queue'.format(process_name)
    task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
        delay_open=True, linger_seconds=0, name=queue_name,
        port=self._task_queue_port,
        timeout_seconds=self._TASK_QUEUE_TIMEOUT_SECONDS)

    process = extraction_process.ExtractionWorkerProcess(
        task_queue, self._processing_configuration, self._system_configurations,
        self._registry_find_specs,
        enable_sigsegv_handler=self._enable_sigsegv_handler, name=process_name)

    # Remove all possible log handlers to prevent a child process from logging
    # to the main process log file and garbling the log. The log handlers are
    # recreated after the worker process has been started.
    for handler in logging.root.handlers:
      logging.root.removeHandler(handler)
      handler.close()

    process.start()

    loggers.ConfigureLogging(
        debug_output=self._debug_output, filename=self._log_filename,
        mode='a', quiet_mode=self._quiet_mode)

    try:
      self._StartMonitoringProcess(process)

    except (IOError, KeyError) as exception:
      pid = process.pid
      logger.error((
          'Unable to monitor replacement worker process: {0:s} '
          '(PID: {1:d}) with error: {2!s}').format(
              process_name, pid, exception))

      self._TerminateProcess(process)
      return None

    self._RegisterProcess(process)

    self._last_worker_number += 1

    return process

  def _StopExtractionProcesses(self, abort=False):
    """Stops the extraction processes.

    Args:
      abort (bool): True to indicated the stop is issued on abort.
    """
    logger.debug('Stopping extraction processes.')
    self._StopMonitoringProcesses()

    if abort:
      # Signal all the processes to abort.
      self._AbortTerminate()

    logger.debug('Emptying task queue.')
    self._task_queue.Empty()

    # Wake the processes to make sure that they are not blocking
    # waiting for the queue new items.
    for _ in self._processes_per_pid:
      try:
        self._task_queue.PushItem(plaso_queue.QueueAbort(), block=False)
      except errors.QueueFull:
        logger.warning('Task queue full, unable to push abort message.')

    # Try waiting for the processes to exit normally.
    self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)
    self._task_queue.Close(abort=abort)

    if not abort:
      # Check if the processes are still alive and terminate them if necessary.
      self._AbortTerminate()
      self._AbortJoin(timeout=self._PROCESS_JOIN_TIMEOUT)
      self._task_queue.Close(abort=True)

    # Kill any lingering processes.
    self._AbortKill()

  def _UpdateForemanProcessStatus(self):
    """Update the foreman process status."""
    used_memory = self._process_information.GetUsedMemory() or 0

    if self._memory_profiler:
      self._memory_profiler.Sample('main', used_memory)

    display_name = getattr(self._merge_task, 'identifier', '')

    self._processing_status.UpdateForemanStatus(
        self._name, self._status, self._pid, used_memory, display_name,
        self._number_of_consumed_sources, self._number_of_produced_sources,
        self._number_of_consumed_event_data,
        self._number_of_produced_event_data,
        0, self._number_of_produced_events, 0, 0, 0, 0)

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

    processing_status = process_status.get('processing_status', None)

    self._RaiseIfNotMonitored(pid)

    display_name = process_status.get('display_name', '')

    number_of_consumed_event_data = process_status.get(
        'number_of_consumed_event_data', None)
    number_of_produced_event_data = process_status.get(
        'number_of_produced_event_data', None)

    number_of_consumed_events = process_status.get(
        'number_of_consumed_events', None)
    number_of_produced_events = process_status.get(
        'number_of_produced_events', None)

    number_of_consumed_sources = process_status.get(
        'number_of_consumed_sources', None)
    number_of_produced_sources = process_status.get(
        'number_of_produced_sources', None)

    if processing_status != definitions.STATUS_INDICATOR_IDLE:
      last_activity_timestamp = process_status.get(
          'last_activity_timestamp', 0.0)

      if last_activity_timestamp:
        last_activity_timestamp += self._worker_timeout

        current_timestamp = time.time()
        if current_timestamp > last_activity_timestamp:
          logger.error((
              'Process {0:s} (PID: {1:d}) has not reported activity within '
              'the timeout period.').format(process.name, pid))
          processing_status = definitions.STATUS_INDICATOR_NOT_RESPONDING

    self._processing_status.UpdateWorkerStatus(
        process.name, processing_status, pid, used_memory, display_name,
        number_of_consumed_sources, number_of_produced_sources,
        number_of_consumed_event_data, number_of_produced_event_data,
        number_of_consumed_events, number_of_produced_events,
        0, 0, 0, 0)

    task_identifier = process_status.get('task_identifier', '')
    if not task_identifier:
      return

    try:
      self._task_manager.UpdateTaskAsProcessingByIdentifier(task_identifier)
      return
    except KeyError:
      logger.debug(
          'Worker {0:s} is processing unknown task: {1:s}.'.format(
              process.name, task_identifier))

  def _UpdateStatus(self):
    """Updates the status."""
    # Make a local copy of the PIDs in case the dict is changed by
    # the main thread.
    for pid in list(self._process_information_per_pid.keys()):
      self._CheckStatusWorkerProcess(pid)

    self._UpdateForemanProcessStatus()

    tasks_status = self._task_manager.GetStatusInformation()
    if self._task_queue_profiler:
      self._task_queue_profiler.Sample(tasks_status)

    self._processing_status.UpdateTasksStatus(tasks_status)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def ProcessSourceMulti(
      self, storage_writer, session_identifier, processing_configuration,
      system_configurations, file_system_path_specs,
      enable_sigsegv_handler=False, storage_file_path=None):
    """Processes file systems within a source.

    Args:
      storage_writer (StorageWriter): storage writer for a session storage.
      session_identifier (str): the identifier of the session the tasks are
          part of.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      system_configurations (list[SystemConfigurationArtifact]): system
          configurations.
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      storage_file_path (Optional[str]): path to the session storage file.

    Returns:
      ProcessingStatus: processing status.

    Raises:
      BadConfigOption: if an invalid collection filter was specified or if
          the preferred time zone is invalid.
    """
    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._system_configurations = system_configurations

    if not self._artifacts_registry:
      # TODO: refactor.
      self.BuildArtifactsRegistry(
          processing_configuration.artifact_definitions_path,
          processing_configuration.custom_artifacts_path)

    # TODO: get environment_variables per system_configuration
    environment_variables = self.knowledge_base.GetEnvironmentVariables()
    user_accounts = list(storage_writer.GetAttributeContainers('user_account'))

    try:
      self.BuildCollectionFilters(
          environment_variables, user_accounts,
          artifact_filter_names=processing_configuration.artifact_filters,
          filter_file_path=processing_configuration.filter_file)
    except errors.InvalidFilter as exception:
      raise errors.BadConfigOption(
          'Unable to build collection filters with error: {0!s}'.format(
              exception))

    self._event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=processing_configuration.data_location,
        preferred_year=processing_configuration.preferred_year,
        system_configurations=system_configurations)

    try:
      self._event_data_timeliner.SetPreferredTimeZone(
          processing_configuration.preferred_time_zone)
    except ValueError as exception:
      raise errors.BadConfigOption(exception)

    # Keep track of certain values so we can spawn new extraction workers.
    self._processing_configuration = processing_configuration

    self._debug_output = processing_configuration.debug_output
    self._log_filename = processing_configuration.log_filename
    self._storage_file_path = storage_file_path
    self._storage_writer = storage_writer
    self._task_storage_format = processing_configuration.task_storage_format

    # Set up the task queue.
    task_outbound_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        delay_open=True, linger_seconds=0, maximum_items=1,
        name='main_task_queue',
        timeout_seconds=self._ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS)
    self._task_queue = task_outbound_queue

    # The ZeroMQ backed queue must be started first, so we can save its port.
    # TODO: raises: attribute-defined-outside-init
    # self._task_queue.name = 'Task queue'
    self._task_queue.Open()
    self._task_queue_port = self._task_queue.port

    # Set up the task storage before the worker processes.
    self._StartTaskStorage(self._task_storage_format)

    for worker_number in range(self._number_of_worker_processes):
      process_name = 'Worker_{0:02d}'.format(self._last_worker_number)
      worker_process = self._StartWorkerProcess(process_name)
      if not worker_process:
        logger.error('Unable to create worker process: {0:d}'.format(
            worker_number))

    self._StartProfiling(self._processing_configuration.profiling)
    self._task_manager.StartProfiling(
        self._processing_configuration.profiling, self._name)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      storage_writer.SetStorageProfiler(self._storage_profiler)

    self._StartStatusUpdateThread()

    try:
      self._ProcessSource(
          storage_writer, session_identifier, file_system_path_specs)

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

      if self._serializers_profiler:
        storage_writer.SetSerializersProfiler(None)

      if self._storage_profiler:
        storage_writer.SetStorageProfiler(None)

      self._task_manager.StopProfiling()
      self._StopProfiling()

    try:
      self._StopExtractionProcesses(abort=self._abort)

    except KeyboardInterrupt:
      self._AbortKill()

      # The abort can leave the main process unresponsive
      # due to incorrectly finalized IPC.
      self._KillProcess(os.getpid())

    # The task queue should be closed by _StopExtractionProcesses, this
    # close is a failsafe.
    self._task_queue.Close(abort=True)

    if self._processing_status.error_path_specs:
      task_storage_abort = True
    else:
      task_storage_abort = self._abort

    try:
      self._StopTaskStorage(
          self._task_storage_format, session_identifier,
          abort=task_storage_abort)
    except (IOError, OSError) as exception:
      logger.error('Unable to stop task storage with error: {0!s}'.format(
          exception))

    if self._abort:
      logger.debug('Processing aborted.')
      self._processing_status.aborted = True
    else:
      logger.debug('Processing completed.')

    # Update the status view one last time.
    self._UpdateStatus()

    # Reset values.
    self._enable_sigsegv_handler = None
    self._event_data_timeliner = None
    self._file_system_cache = []
    self._processing_configuration = None
    self._storage_file_path = None
    self._storage_writer = None
    self._system_configurations = None
    self._task_storage_format = None

    return self._processing_status
