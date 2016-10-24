# -*- coding: utf-8 -*-
"""The multi-process worker process."""

import logging

from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import context

from plaso.engine import plaso_queue
from plaso.engine import profiler
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import base_process
from plaso.parsers import mediator as parsers_mediator


class WorkerProcess(base_process.MultiProcessBaseProcess):
  """Class that defines a multi-processing worker process."""

  def __init__(
      self, task_queue, storage_writer, knowledge_base, session_identifier,
      debug_output=False, enable_profiling=False, filter_object=None,
      hasher_names_string=None, mount_path=None, parser_filter_expression=None,
      preferred_year=None, process_archives=False,
      process_compressed_streams=True, profiling_directory=None,
      profiling_sample_rate=1000, profiling_type=u'all',
      temporary_directory=None, text_prepend=None, yara_rules_string=None,
      **kwargs):
    """Initializes a worker process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      task_queue (PlasoQueue): task queue.
      storage_writer (StorageWriter): storage writer for a session storage.
      knowledge_base (KnowledgeBase): knowledge base which contains
          information from the source data needed for parsing.
      session_identifier (str): identifier of the session.
      debug_output (Optional[bool]): True if debug output should be enabled.
      enable_profiling (Optional[bool]): True if profiling should be enabled.
      filter_object (Optional[objectfilter.Filter]): filter object.
      hasher_names_string (Optional[str]): comma separated string of names
          of hashers to use during processing.
      mount_path (Optional[str]): mount path.
      parser_filter_expression (Optional[str]): parser filter expression,
          where None represents all parsers and plugins.
      preferred_year (Optional[int]): preferred year.
      process_archives (Optional[bool]): True if archive files should be
          scanned for file entries.
      process_compressed_streams (Optional[bool]): True if file content in
          compressed streams should be processed.
      profiling_directory (Optional[str]): path to the directory where
          the profiling sample files should be stored.
      profiling_sample_rate (Optional[int]): the profiling sample rate.
          Contains the number of event sources processed.
      profiling_type (Optional[str]): type of profiling.
          Supported types are:

          * 'memory' to profile memory usage;
          * 'parsers' to profile CPU time consumed by individual parsers;
          * 'processing' to profile CPU time consumed by different parts of
            the processing;
          * 'serializers' to profile CPU time consumed by individual
            serializers.
      temporary_directory (Optional[str]): path of the directory for temporary
          files.
      text_prepend (Optional[str]): text to prepend to every event.
      yara_rules_string (Optional[str]): unparsed yara rule definitions.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(WorkerProcess, self).__init__(**kwargs)
    self._abort = False
    self._buffer_size = 0
    self._current_display_name = u''
    self._debug_output = debug_output
    self._enable_profiling = enable_profiling
    self._extraction_worker = None
    self._filter_object = filter_object
    self._hasher_names_string = hasher_names_string
    self._knowledge_base = knowledge_base
    self._memory_profiler = None
    self._mount_path = mount_path
    self._number_of_consumed_events = 0
    self._number_of_consumed_sources = 0
    self._parser_filter_expression = parser_filter_expression
    self._parser_mediator = None
    self._parsers_profiler = None
    self._preferred_year = preferred_year
    self._process_archives = process_archives
    self._process_compressed_streams = process_compressed_streams
    self._processing_profiler = None
    self._profiling_directory = profiling_directory
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type
    self._serializers_profiler = None
    self._session_identifier = session_identifier
    self._status = definitions.PROCESSING_STATUS_INITIALIZED
    self._storage_writer = storage_writer
    self._task = None
    self._task_queue = task_queue
    self._temporary_directory = temporary_directory
    self._text_prepend = text_prepend
    self._yara_rules_string = yara_rules_string

  def _GetStatus(self):
    """Returns status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    if self._parser_mediator:
      number_of_produced_errors = (
          self._parser_mediator.number_of_produced_errors)
      number_of_produced_events = (
          self._parser_mediator.number_of_produced_events)
      number_of_produced_sources = (
          self._parser_mediator.number_of_produced_event_sources)
    else:
      number_of_produced_errors = None
      number_of_produced_events = None
      number_of_produced_sources = None

    if self._extraction_worker:
      last_activity_timestamp = self._extraction_worker.last_activity_timestamp
      processing_status = self._extraction_worker.processing_status
    else:
      last_activity_timestamp = 0.0
      processing_status = self._status

    task_identifier = getattr(self._task, u'identifier', u'')

    status = {
        u'display_name': self._current_display_name,
        u'identifier': self._name,
        u'number_of_consumed_errors': None,
        u'number_of_consumed_event_tags': None,
        u'number_of_consumed_events': self._number_of_consumed_events,
        u'number_of_consumed_sources': self._number_of_consumed_sources,
        u'number_of_produced_errors': number_of_produced_errors,
        u'number_of_produced_event_tags': None,
        u'number_of_produced_events': number_of_produced_events,
        u'number_of_produced_sources': number_of_produced_sources,
        u'last_activity_timestamp': last_activity_timestamp,
        u'processing_status': processing_status,
        u'task_identifier': task_identifier}

    return status

  def _Main(self):
    """The main loop."""
    self._parser_mediator = parsers_mediator.ParserMediator(
        None, self._knowledge_base, preferred_year=self._preferred_year,
        temporary_directory=self._temporary_directory)

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
        process_archives=self._process_archives,
        process_compressed_streams=self._process_compressed_streams)

    if self._hasher_names_string:
      self._extraction_worker.SetHashers(self._hasher_names_string)

    if self._yara_rules_string:
      self._extraction_worker.SetYaraRules(self._yara_rules_string)

    self._StartProfiling()

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

    # All exceptions need to be caught here to prevent the process
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      logging.warning(
          u'Unhandled exception in process: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logging.exception(exception)

      self._abort = True

    self._StopProfiling()
    self._extraction_worker = None
    self._parser_mediator = None
    self._storage_writer = None

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

    logging.debug(u'Worker: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    try:
      self._task_queue.Close(abort=self._abort)
    except errors.QueueAlreadyClosed:
      logging.error(u'Queue for {0:s} was already closed.'.format(self.name))

  def _ProcessPathSpec(self, extraction_worker, parser_mediator, path_spec):
    """Processes a path specification.

    Args:
      extraction_worker (worker.ExtractionWorker): extraction worker.
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
    """
    self._current_display_name = parser_mediator.GetDisplayNameForPathSpec(
        path_spec)

    try:
      extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

    except dfvfs_errors.CacheFullError:
      # TODO: signal engine of failure.
      self._abort = True
      logging.error((
          u'ABORT: detected cache full error while processing '
          u'path spec: {0:s}').format(self._current_display_name))

    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionError((
          u'unable to process path specification with error: '
          u'{0:s}').format(exception), path_spec=path_spec)

      if self._debug_output:
        logging.warning(
            u'Unhandled exception while processing path spec: {0:s}.'.format(
                self._current_display_name))
        logging.exception(exception)

  def _ProcessTask(self, task):
    """Processes a task.

    Args:
      task (Task): task.
    """
    self._task = task

    storage_writer = self._storage_writer.CreateTaskStorage(task)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    storage_writer.Open()

    self._parser_mediator.SetStorageWriter(storage_writer)

    storage_writer.WriteTaskStart()

    try:
      # TODO: add support for more task types.
      self._ProcessPathSpec(
          self._extraction_worker, self._parser_mediator, task.path_spec)
      self._number_of_consumed_sources += 1

      if self._memory_profiler:
        self._memory_profiler.Sample()

    finally:
      storage_writer.WriteTaskCompletion(aborted=self._abort)

      self._parser_mediator.SetStorageWriter(None)

      storage_writer.Close()

    try:
      self._storage_writer.PrepareMergeTaskStorage(task)
    except IOError:
      pass

    self._task = None

  def _StartProfiling(self):
    """Starts profiling."""
    if not self._enable_profiling:
      return

    if self._profiling_type in (u'all', u'memory'):
      identifier = u'{0:s}-memory'.format(self._name)
      self._memory_profiler = profiler.GuppyMemoryProfiler(
          identifier, path=self._profiling_directory,
          profiling_sample_rate=self._profiling_sample_rate)
      self._memory_profiler.Start()

    if self._profiling_type in (u'all', u'parsers'):
      identifier = u'{0:s}-parsers'.format(self._name)
      self._parsers_profiler = profiler.ParsersProfiler(
          identifier, path=self._profiling_directory)
      self._extraction_worker.SetParsersProfiler(self._parsers_profiler)

    if self._profiling_type in (u'all', u'processing'):
      identifier = u'{0:s}-processing'.format(self._name)
      self._processing_profiler = profiler.ProcessingProfiler(
          identifier, path=self._profiling_directory)
      self._extraction_worker.SetProcessingProfiler(self._processing_profiler)

    if self._profiling_type in (u'all', u'serializers'):
      identifier = u'{0:s}-serializers'.format(self._name)
      self._serializers_profiler = profiler.SerializersProfiler(
          identifier, path=self._profiling_directory)

  def _StopProfiling(self):
    """Stops profiling."""
    if not self._enable_profiling:
      return

    if self._profiling_type in (u'all', u'memory'):
      self._memory_profiler.Sample()
      self._memory_profiler = None

    if self._profiling_type in (u'all', u'parsers'):
      self._extraction_worker.SetParsersProfiler(None)
      self._parsers_profiler.Write()
      self._parsers_profiler = None

    if self._profiling_type in (u'all', u'processing'):
      self._extraction_worker.SetProcessingProfiler(None)
      self._processing_profiler.Write()
      self._processing_profiler = None

    if self._profiling_type in (u'all', u'serializers'):
      self._serializers_profiler.Write()
      self._serializers_profiler = None

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
    if self._extraction_worker:
      self._extraction_worker.SignalAbort()
    if self._parser_mediator:
      self._parser_mediator.SignalAbort()
