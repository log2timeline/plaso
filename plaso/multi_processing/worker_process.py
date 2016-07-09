# -*- coding: utf-8 -*-
"""The multi-process worker process."""
import logging

from dfvfs.resolver import context

from plaso.engine import worker, plaso_queue
from plaso.lib import definitions, errors
from plaso.multi_processing import base_process
from plaso.multi_processing import multi_process_queue
from plaso.parsers import mediator as parsers_mediator

class WorkerProcess(base_process.MultiProcessBaseProcess):
  """Class that defines a multi-processing worker process."""

  def __init__(
      self, task_queue, storage_writer, knowledge_base, session_identifier,
      worker_number, enable_debug_output=False, enable_profiling=False,
      filter_object=None, hasher_names_string=None, mount_path=None,
      parser_filter_expression=None, process_archive_files=False,
      profiling_sample_rate=1000, profiling_type=u'all', text_prepend=None,
      **kwargs):
    """Initializes the process object.

    Args:
      task_queue: the task queue object (instance of MultiProcessingQueue).
      storage_writer: a storage writer object (instance of StorageWriter).
      knowledge_base: a knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
      session_identifier: a string containing the identifier of the session.
      worker_number: a number that identifies the worker.
      enable_debug_output: optional boolean value to indicate if the debug
                           output should be enabled.
      enable_profiling: optional boolean value to indicate if profiling should
                        be enabled.
      filter_object: optional filter object (instance of objectfilter.Filter).
      hasher_names_string: optional comma separated string of names of
                           hashers to enable enable.
      mount_path: optional string containing the mount path. The default
                  is None.
      parser_filter_expression: optional string containing the parser filter
                                expression, where None represents all parsers
                                and plugins.
      process_archive_files: optional boolean value to indicate if the worker
                             should scan for file entries inside files.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
      profiling_type: optional profiling type.
      text_prepend: optional string that contains the text to prepend to every
                    event object.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(WorkerProcess, self).__init__(**kwargs)
    self._abort = False
    self._buffer_size = 0
    self._critical_error = False
    self._enable_debug_output = enable_debug_output
    self._extraction_worker = None
    self._knowledge_base = knowledge_base
    self._number_of_consumed_sources = 0
    self._parser_mediator = None
    self._session_identifier = session_identifier
    self._status = definitions.PROCESSING_STATUS_INITIALIZED
    self._storage_writer = storage_writer
    self._task_queue = task_queue
    self._worker_number = worker_number

    # Attributes for profiling.
    self._enable_profiling = enable_profiling
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

    # TODO: clean this up with the implementation of a task based
    # multi-processing approach.
    self._filter_object = filter_object
    self._hasher_names_string = hasher_names_string
    self._mount_path = mount_path
    self._parser_filter_expression = parser_filter_expression
    self._process_archive_files = process_archive_files
    self._text_prepend = text_prepend

  def _GetStatus(self):
    """Returns a status dictionary."""
    if self._parser_mediator:
      number_of_produced_events = (
          self._parser_mediator.number_of_produced_events)
      number_of_produced_sources = (
          self._parser_mediator.number_of_produced_event_sources)
    else:
      number_of_produced_events = 0
      number_of_produced_sources = 0

    processing_status = self._extraction_worker.processing_status
    if processing_status == definitions.PROCESSING_STATUS_IDLE:
      processing_status = self._status

    # TODO: add number of consumed events.
    status = {
        u'number_of_consumed_events': 0,
        u'number_of_consumed_sources': self._number_of_consumed_sources,
        u'display_name': self._extraction_worker.current_display_name,
        u'identifier': self._name,
        u'processing_status': processing_status,
        u'number_of_produced_events': number_of_produced_events,
        u'number_of_produced_sources': number_of_produced_sources}

    if self._critical_error:
      # Note seem unable to pass objects here.
      current_path_spec = self._extraction_worker.current_path_spec
      status[u'path_spec'] = current_path_spec.comparable
      status[u'processing_status'] = definitions.PROCESSING_STATUS_ERROR

    self._status_is_running = status.get(u'is_running', False)
    return status

  def _ProcessTask(self, task):
    """Processes a task.

    Args:
      task (Task): task.
    """
    storage_writer = self._storage_writer.CreateTaskStorage(task)

    if self._enable_profiling:
      storage_writer.EnableProfiling(profiling_type=self._profiling_type)

    storage_writer.Open()

    try:
      self._parser_mediator.SetStorageWriter(storage_writer)

      storage_writer.WriteTaskStart()

      # TODO: add support for more task types.
      self._extraction_worker.ProcessPathSpec(
          self._parser_mediator, task.path_spec)
      self._number_of_consumed_sources += 1

      # TODO: on abort use WriteTaskAborted instead of completion?
      storage_writer.WriteTaskCompletion()

    finally:
      self._parser_mediator.SetStorageWriter(None)

      storage_writer.Close()

      if self._enable_profiling:
        storage_writer.DisableProfiling()

    self._storage_writer.PrepareMergeTaskStorage(task.identifier)

  def _Main(self):
    """The main loop."""
    self._parser_mediator = parsers_mediator.ParserMediator(
        None, self._knowledge_base)

    if self._filter_object:
      self._parser_mediator.SetFilterObject(self._filter_object)

    if self._mount_path:
      self._parser_mediator.SetMountPath(self._mount_path)

    if self._text_prepend:
      self._parser_mediator.SetTextPrepend(self._text_prepend)

    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    resolver_context = context.Context()

    # We need to initialize the parser and hasher objects after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    self._extraction_worker = worker.EventExtractionWorker(
        resolver_context,
        parser_filter_expression=self._parser_filter_expression,
        process_archive_files=self._process_archive_files)

    # TODO: differentiate between debug output and debug mode.
    self._extraction_worker.SetEnableDebugMode(self._enable_debug_output)

    if self._hasher_names_string:
      self._extraction_worker.SetHashers(self._hasher_names_string)

    if self._enable_profiling:
      self._extraction_worker.EnableProfiling(
          profiling_sample_rate=self._profiling_sample_rate,
          profiling_type=self._profiling_type)

    self._extraction_worker.ProfilingStart(self._name)

    logging.debug(u'Worker: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    self._status = definitions.PROCESSING_STATUS_RUNNING

    try:
      logging.debug(
          u'{0!s} (PID: {1:d}) started monitoring task queue.'.format(
              self._name, self._pid))

      while not self._abort:
        try:
          task = self._task_queue.PopItem()
        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logging.debug(u'ConsumeItems exiting with exception {0:s}.'.format(
              type(exception)))
          break

        if isinstance(task, plaso_queue.QueueAbort):
          logging.debug(u'ConsumeItems exiting, dequeued QueueAbort object.')
          break

        self._ProcessTask(task)

      logging.debug(
          u'{0!s} (PID: {1:d}) stopped monitoring task queue.'.format(
              self._name, self._pid))

    except Exception as exception:  # pylint: disable=broad-except
      logging.warning(
          u'Unhandled exception in worker: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logging.exception(exception)

      self._abort = True

    self._extraction_worker.ProfilingStop()
    self._extraction_worker = None
    self._parser_mediator = None

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

    logging.debug(u'Extraction worker: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    if isinstance(self._task_queue, multi_process_queue.MultiProcessingQueue):
      self._task_queue.Close(abort=True)
    else:
      self._task_queue.Close()

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
    self._extraction_worker.SignalAbort()
    self._parser_mediator.SignalAbort()
