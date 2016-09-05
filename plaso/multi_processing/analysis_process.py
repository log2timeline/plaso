# -*- coding: utf-8 -*-
"""The multi-process analysis process."""

import logging

from plaso.analysis import mediator as analysis_mediator
from plaso.containers import tasks
from plaso.engine import plaso_queue
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import base_process


class AnalysisProcess(base_process.MultiProcessBaseProcess):
  """Class that defines a multi-processing analysis process."""

  def __init__(
      self, event_queue, storage_writer, knowledge_base, analysis_plugin,
      data_location=None, event_filter_expression=None, **kwargs):
    """Initializes an analysis process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      event_queue (Queue): event queue.
      storage_writer (StorageWriter): storage writer for a session storage.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for analysis.
      plugin (AnalysisProcess): plugin running in the process.
      data_location (Optional[str]): path to the location that data files
          should be loaded from.
      event_filter_expression (Optional[str]): event filter expression.
    """
    super(AnalysisProcess, self).__init__(**kwargs)
    self._abort = False
    self._analysis_mediator = None
    self._analysis_plugin = analysis_plugin
    self._data_location = data_location
    self._debug_output = False
    self._event_filter_expression = event_filter_expression
    self._event_queue = event_queue
    self._knowledge_base = knowledge_base
    self._memory_profiler = None
    self._number_of_consumed_events = 0
    self._serializers_profiler = None
    self._status = definitions.PROCESSING_STATUS_INITIALIZED
    self._storage_writer = storage_writer
    self._task_identifier = u''

  def _GetStatus(self):
    """Returns status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    if self._analysis_mediator:
      number_of_produced_reports = (
          self._analysis_mediator.number_of_produced_analysis_reports)
    else:
      number_of_produced_reports = None

    status = {
        u'display_name': u'',
        u'identifier': self._name,
        u'number_of_consumed_errors': None,
        u'number_of_consumed_events': self._number_of_consumed_events,
        u'number_of_consumed_reports': None,
        u'number_of_consumed_sources': None,
        u'number_of_produced_errors': None,
        u'number_of_produced_events': None,
        u'number_of_produced_reports': number_of_produced_reports,
        u'number_of_produced_sources': None,
        u'processing_status': self._status,
        u'task_identifier': None}

    return status

  def _Main(self):
    """The main loop."""
    logging.debug(u'Analysis plugin: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    self._status = definitions.PROCESSING_STATUS_ANALYZING

    task = tasks.Task()
    # TODO: temporary solution.
    task.identifier = self._analysis_plugin.plugin_name

    self._task_identifier = task.identifier

    storage_writer = self._storage_writer.CreateTaskStorage(task)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    storage_writer.Open()

    self._analysis_mediator = analysis_mediator.AnalysisMediator(
        storage_writer, self._knowledge_base, data_location=self._data_location)

    # TODO: set event_filter_expression in mediator.

    storage_writer.WriteTaskStart()

    try:
      logging.debug(
          u'{0!s} (PID: {1:d}) started monitoring event queue.'.format(
              self._name, self._pid))

      while not self._abort:
        try:
          event = self._event_queue.PopItem()

        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logging.debug(u'ConsumeItems exiting with exception {0:s}.'.format(
              type(exception)))
          break

        if isinstance(event, plaso_queue.QueueAbort):
          logging.debug(u'ConsumeItems exiting, dequeued QueueAbort object.')
          break

        self._ProcessEvent(self._analysis_mediator, event)

        self._number_of_consumed_events += 1

        if self._memory_profiler:
          self._memory_profiler.Sample()

      logging.debug(
          u'{0!s} (PID: {1:d}) stopped monitoring event queue.'.format(
              self._name, self._pid))

      if not self._abort:
        self._status = definitions.PROCESSING_STATUS_REPORTING

        self._analysis_mediator.ProduceAnalysisReport(self._analysis_plugin)

    # All exceptions need to be caught here to prevent the process
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      logging.warning(
          u'Unhandled exception in process: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logging.exception(exception)

      self._abort = True

    finally:
      storage_writer.WriteTaskCompletion(aborted=self._abort)

      storage_writer.Close()

    try:
      self._storage_writer.PrepareMergeTaskStorage(task.identifier)
    except IOError:
      pass

    self._analysis_mediator = None
    self._storage_writer = None
    self._task_identifier = u''

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

    logging.debug(u'Analysis plugin: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    try:
      self._event_queue.Close(abort=self._abort)
    except errors.QueueAlreadyClosed:
      logging.error(u'Queue for {0:s} was already closed.'.format(self.name))

  def _ProcessEvent(self, mediator, event):
    """Processes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
    """
    try:
      self._analysis_plugin.ExamineEvent(mediator, event)

    except Exception as exception:  # pylint: disable=broad-except
      # TODO: write analysis error.

      if self._debug_output:
        logging.warning(u'Unhandled exception while processing event object.')
        logging.exception(exception)

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
