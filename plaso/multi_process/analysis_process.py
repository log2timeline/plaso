# -*- coding: utf-8 -*-
"""The multi-process analysis worker process."""

import threading

from plaso.analysis import mediator as analysis_mediator
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_process import logger
from plaso.multi_process import plaso_queue
from plaso.multi_process import task_process


class AnalysisProcess(task_process.MultiProcessTaskProcess):
  """Multi-processing analysis worker process."""

  # Number of seconds to wait for the completion status to be queried
  # by the foreman process.
  _FOREMAN_STATUS_WAIT = 5 * 60

  def __init__(
      self, event_queue, analysis_plugin, processing_configuration,
      user_accounts, data_location=None, event_filter_expression=None,
      **kwargs):
    """Initializes an analysis worker process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      event_queue (plaso_queue.Queue): event queue.
      analysis_plugin (AnalysisPlugin): plugin running in the process.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      user_accounts (list[UserAccountArtifact]): user accounts.
      data_location (Optional[str]): path to the location that data files
          should be loaded from.
      event_filter_expression (Optional[str]): event filter expression.
    """
    super(AnalysisProcess, self).__init__(processing_configuration, **kwargs)
    self._abort = False
    self._analysis_mediator = None
    self._analysis_plugin = analysis_plugin
    self._data_location = data_location
    self._event_filter_expression = event_filter_expression
    self._event_queue = event_queue
    self._foreman_status_wait_event = None
    self._number_of_consumed_events = 0
    self._status = definitions.STATUS_INDICATOR_INITIALIZED
    self._task = None
    self._user_accounts = user_accounts

  def _GetStatus(self):
    """Retrieves status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    logger.debug('Status update requested')

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

    # XML RPC does not support integer values > 2 GiB so we format them
    # as a string.
    used_memory = '{0:d}'.format(used_memory)

    status = {
        'display_name': '',
        'identifier': self._name,
        'number_of_consumed_event_data': None,
        'number_of_consumed_event_tags': None,
        'number_of_consumed_events': self._number_of_consumed_events,
        'number_of_consumed_reports': None,
        'number_of_consumed_sources': None,
        'number_of_produced_event_data': None,
        'number_of_produced_event_tags': number_of_produced_event_tags,
        'number_of_produced_events': None,
        'number_of_produced_reports': number_of_produced_reports,
        'number_of_produced_sources': None,
        'processing_status': self._status,
        'task_identifier': None,
        'used_memory': used_memory}

    if self._status in (
        definitions.STATUS_INDICATOR_ABORTED,
        definitions.STATUS_INDICATOR_COMPLETED):
      logger.debug('Set foreman status wait event')
      self._foreman_status_wait_event.set()

    return status

  def _Main(self):
    """The main loop."""
    self._StartProfiling(self._processing_configuration.profiling)

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

    task_storage_writer = self._storage_factory.CreateTaskStorageWriter(
        definitions.STORAGE_FORMAT_SQLITE)

    if self._serializers_profiler:
      task_storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      task_storage_writer.SetStorageProfiler(self._storage_profiler)

    storage_file_path = self._GetTaskStorageFilePath(
        definitions.STORAGE_FORMAT_SQLITE, task)
    task_storage_writer.Open(path=storage_file_path)

    self._analysis_mediator = analysis_mediator.AnalysisMediator(
        data_location=self._data_location, user_accounts=self._user_accounts)

    # TODO: move into analysis process.
    self._analysis_mediator.SetStorageWriter(task_storage_writer)

    # TODO: set event_filter_expression in mediator.

    task_storage_writer.AddAttributeContainer(task)

    try:
      logger.debug(
          '{0!s} (PID: {1:d}) started monitoring event queue.'.format(
              self._name, self._pid))

      while not self._abort:
        try:
          queued_object = self._event_queue.PopItem()

        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logger.debug('ConsumeItems exiting with exception {0!s}.'.format(
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
      task.aborted = self._abort
      task_storage_writer.UpdateAttributeContainer(task)

      task_storage_writer.Close()

      if self._serializers_profiler:
        task_storage_writer.SetSerializersProfiler(None)

      if self._storage_profiler:
        task_storage_writer.SetStorageProfiler(None)

    try:
      self._FinalizeTaskStorageWriter(
          definitions.STORAGE_FORMAT_SQLITE, task)
    except IOError as exception:
      logger.warning('Unable to finalize task storage with error: {0!s}'.format(
          exception))

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    logger.debug('Wait for foreman status wait event')
    self._foreman_status_wait_event.clear()
    self._foreman_status_wait_event.wait(self._FOREMAN_STATUS_WAIT)

    logger.debug('Analysis plugin: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    self._StopProfiling()

    self._analysis_mediator = None
    self._foreman_status_wait_event = None
    self._task = None

    try:
      self._event_queue.Close(abort=self._abort)
    except errors.QueueAlreadyClosed:
      logger.error('Queue for {0:s} was already closed.'.format(self.name))

  def _ProcessEvent(self, mediator, event, event_data, event_data_stream):
    """Processes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    try:
      self._analysis_plugin.ExamineEvent(
          mediator, event, event_data, event_data_stream)

    except Exception as exception:  # pylint: disable=broad-except
      # TODO: write analysis error and change logger to debug only.

      logger.warning('Unhandled exception while processing event object.')
      logger.exception(exception)

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True

    if self._foreman_status_wait_event:
      logger.debug('Abort foreman status wait event')
      self._foreman_status_wait_event.set()

    if self._analysis_mediator:
      self._analysis_mediator.SignalAbort()
