# -*- coding: utf-8 -*-
"""The multi-process analysis process."""

from __future__ import unicode_literals

import threading

from plaso.analysis import mediator as analysis_mediator
from plaso.containers import tasks
from plaso.engine import plaso_queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import base_process
from plaso.multi_processing import logger


class AnalysisProcess(base_process.MultiProcessBaseProcess):
  """Multi-processing analysis process."""

  # Number of seconds to wait for the completion status to be queried
  # by the foreman process.
  _FOREMAN_STATUS_WAIT = 5 * 60

  def __init__(
      self, event_queue, storage_writer, knowledge_base, analysis_plugin,
      processing_configuration, data_location=None,
      event_filter_expression=None, **kwargs):
    """Initializes an analysis process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      event_queue (plaso_queue.Queue): event queue.
      storage_writer (StorageWriter): storage writer for a session storage.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for analysis.
      analysis_plugin (AnalysisPlugin): plugin running in the process.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      data_location (Optional[str]): path to the location that data files
          should be loaded from.
      event_filter_expression (Optional[str]): event filter expression.
    """
    super(AnalysisProcess, self).__init__(processing_configuration, **kwargs)
    self._abort = False
    self._analysis_mediator = None
    self._analysis_plugin = analysis_plugin
    self._data_location = data_location
    self._debug_output = False
    self._event_filter_expression = event_filter_expression
    self._event_queue = event_queue
    self._foreman_status_wait_event = None
    self._knowledge_base = knowledge_base
    self._number_of_consumed_events = 0
    self._status = definitions.STATUS_INDICATOR_INITIALIZED
    self._storage_writer = storage_writer
    self._task = None

  def _GetStatus(self):
    """Retrieves status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    if self._analysis_mediator:
      number_of_produced_event_tags = (
          self._analysis_mediator.number_of_produced_event_tags)
      number_of_produced_reports = (
          self._analysis_mediator.number_of_produced_analysis_reports)
    else:
      number_of_produced_event_tags = None
      number_of_produced_reports = None

    if self._process_information:
      used_memory = self._process_information.GetUsedMemory() or 0
    else:
      used_memory = 0

    if self._memory_profiler:
      self._memory_profiler.Sample('main', used_memory)

    status = {
        'display_name': '',
        'identifier': self._name,
        'number_of_consumed_event_tags': None,
        'number_of_consumed_events': self._number_of_consumed_events,
        'number_of_consumed_reports': None,
        'number_of_consumed_sources': None,
        'number_of_consumed_warnings': None,
        'number_of_produced_event_tags': number_of_produced_event_tags,
        'number_of_produced_events': None,
        'number_of_produced_reports': number_of_produced_reports,
        'number_of_produced_sources': None,
        'number_of_produced_warnings': None,
        'processing_status': self._status,
        'task_identifier': None,
        'used_memory': used_memory}

    if self._status in (
        definitions.STATUS_INDICATOR_ABORTED,
        definitions.STATUS_INDICATOR_COMPLETED):
      self._foreman_status_wait_event.set()

    return status

  def _Main(self):
    """The main loop."""
    self._StartProfiling(self._processing_configuration.profiling)

    if self._serializers_profiler:
      self._storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._storage_writer.SetStorageProfiler(self._storage_profiler)

    logger.debug('Analysis plugin: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    # Creating the threading event in the constructor will cause a pickle
    # error on Windows when an analysis process is created.
    self._foreman_status_wait_event = threading.Event()
    self._status = definitions.STATUS_INDICATOR_ANALYZING

    task = tasks.Task()
    task.storage_format = definitions.STORAGE_FORMAT_SQLITE
    # TODO: temporary solution.
    task.identifier = self._analysis_plugin.plugin_name

    self._task = task

    storage_writer = self._storage_writer.CreateTaskStorage(
        task, definitions.STORAGE_FORMAT_SQLITE)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      storage_writer.SetStorageProfiler(self._storage_profiler)

    storage_writer.Open()

    self._analysis_mediator = analysis_mediator.AnalysisMediator(
        storage_writer, self._knowledge_base, data_location=self._data_location)

    # TODO: set event_filter_expression in mediator.

    storage_writer.WriteTaskStart()

    try:
      logger.debug(
          '{0!s} (PID: {1:d}) started monitoring event queue.'.format(
              self._name, self._pid))

      while not self._abort:
        try:
          queued_object = self._event_queue.PopItem()

        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logger.debug('ConsumeItems exiting with exception {0:s}.'.format(
              type(exception)))
          break

        if isinstance(queued_object, plaso_queue.QueueAbort):
          logger.debug('ConsumeItems exiting, dequeued QueueAbort object.')
          break

        self._ProcessEvent(self._analysis_mediator, *queued_object)

        self._number_of_consumed_events += 1

      logger.debug(
          '{0!s} (PID: {1:d}) stopped monitoring event queue.'.format(
              self._name, self._pid))

      if not self._abort:
        self._status = definitions.STATUS_INDICATOR_REPORTING

        self._analysis_mediator.ProduceAnalysisReport(self._analysis_plugin)

    # All exceptions need to be caught here to prevent the process
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      logger.warning(
          'Unhandled exception in process: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logger.exception(exception)

      self._abort = True

    finally:
      storage_writer.WriteTaskCompletion(aborted=self._abort)

      storage_writer.Close()

      if self._serializers_profiler:
        storage_writer.SetSerializersProfiler(None)

      if self._storage_profiler:
        storage_writer.SetStorageProfiler(None)

    try:
      self._storage_writer.FinalizeTaskStorage(task)
    except IOError:
      pass

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    self._foreman_status_wait_event.wait(self._FOREMAN_STATUS_WAIT)

    logger.debug('Analysis plugin: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    if self._serializers_profiler:
      self._storage_writer.SetSerializersProfiler(None)

    if self._storage_profiler:
      self._storage_writer.SetStorageProfiler(None)

    self._StopProfiling()

    self._analysis_mediator = None
    self._foreman_status_wait_event = None
    self._storage_writer = None
    self._task = None

    try:
      self._event_queue.Close(abort=self._abort)
    except errors.QueueAlreadyClosed:
      logger.error('Queue for {0:s} was already closed.'.format(self.name))

  def _ProcessEvent(self, mediator, event, event_data):
    """Processes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
      event_data (EventData): event data.
    """
    try:
      self._analysis_plugin.ExamineEvent(mediator, event, event_data)

    except Exception as exception:  # pylint: disable=broad-except
      self.SignalAbort()

      # TODO: write analysis error.

      if self._debug_output:
        logger.warning('Unhandled exception while processing event object.')
        logger.exception(exception)

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
    if self._foreman_status_wait_event:
      self._foreman_status_wait_event.set()
    if self._analysis_mediator:
      self._analysis_mediator.SignalAbort()
