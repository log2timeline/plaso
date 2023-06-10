# -*- coding: utf-8 -*-
"""The multi-process extraction worker process."""

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_process import logger
from plaso.multi_process import plaso_queue
from plaso.multi_process import task_process
from plaso.parsers import mediator as parsers_mediator


class ExtractionWorkerProcess(task_process.MultiProcessTaskProcess):
  """Multi-processing extraction worker process."""

  # Maximum number of dfVFS file system objects to cache in the worker process.
  _FILE_SYSTEM_CACHE_SIZE = 3

  def __init__(
      self, task_queue, processing_configuration, system_configurations,
      registry_find_specs, **kwargs):
    """Initializes an extraction worker process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      task_queue (PlasoQueue): task queue.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      system_configurations (list[SystemConfigurationArtifact]): system
          configurations.
     registry_find_specs (list[dfwinreg.FindSpec]): Windows Registry find
         specifications.
      kwargs: keyword arguments to pass to multiprocessing.Process.
    """
    super(ExtractionWorkerProcess, self).__init__(
        processing_configuration, **kwargs)
    self._abort = False
    self._buffer_size = 0
    self._current_display_name = ''
    self._extraction_worker = None
    self._file_system_cache = []
    self._number_of_consumed_sources = 0
    self._parser_mediator = None
    self._registry_find_specs = registry_find_specs
    self._resolver_context = None
    self._status = definitions.STATUS_INDICATOR_INITIALIZED
    self._task = None
    self._task_queue = task_queue
    self._system_configurations = system_configurations

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

  def _CreateParserMediator(
      self, resolver_context, processing_configuration, system_configurations):
    """Creates a parser mediator.

    Args:
      resolver_context (dfvfs.Context): resolver context.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      system_configurations (list[SystemConfigurationArtifact]): system
          configurations.

    Returns:
      ParserMediator: parser mediator.
    """
    mediator = parsers_mediator.ParserMediator(
        registry_find_specs=self._registry_find_specs,
        resolver_context=resolver_context,
        system_configurations=system_configurations)

    mediator.SetExtractWinEvtResources(
        processing_configuration.extraction.extract_winevt_resources)
    mediator.SetPreferredCodepage(processing_configuration.preferred_codepage)
    mediator.SetPreferredLanguage(processing_configuration.preferred_language)
    mediator.SetTemporaryDirectory(processing_configuration.temporary_directory)

    return mediator

  def _GetStatus(self):
    """Retrieves status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    if self._parser_mediator:
      number_of_produced_event_data = (
          self._parser_mediator.number_of_produced_event_data)
      number_of_produced_sources = (
          self._parser_mediator.number_of_produced_event_sources)
    else:
      number_of_produced_event_data = None
      number_of_produced_sources = None

    if self._extraction_worker and self._parser_mediator:
      last_activity_timestamp = max(
          self._extraction_worker.last_activity_timestamp,
          self._parser_mediator.last_activity_timestamp)
      processing_status = self._extraction_worker.processing_status
    else:
      last_activity_timestamp = 0.0
      processing_status = self._status

    task_identifier = getattr(self._task, 'identifier', '')

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
        'display_name': self._current_display_name,
        'identifier': self._name,
        'last_activity_timestamp': last_activity_timestamp,
        'number_of_consumed_event_data': None,
        'number_of_consumed_event_tags': None,
        'number_of_consumed_events': None,
        'number_of_consumed_sources': self._number_of_consumed_sources,
        'number_of_produced_event_data': number_of_produced_event_data,
        'number_of_produced_event_tags': None,
        'number_of_produced_events': None,
        'number_of_produced_sources': number_of_produced_sources,
        'processing_status': processing_status,
        'task_identifier': task_identifier,
        'used_memory': used_memory}

    return status

  def _Main(self):
    """The main loop."""
    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    self._resolver_context = context.Context()

    for credential_configuration in self._processing_configuration.credentials:
      path_spec_resolver.Resolver.key_chain.SetCredential(
          credential_configuration.path_spec,
          credential_configuration.credential_type,
          credential_configuration.credential_data)

    self._parser_mediator = self._CreateParserMediator(
        self._resolver_context, self._processing_configuration,
        self._system_configurations)

    # We need to initialize the parser and hasher objects after the process
    # has forked otherwise on Windows the "fork" will fail with
    # a PickleError for Python modules that cannot be pickled.
    self._extraction_worker = worker.EventExtractionWorker(
        parser_filter_expression=(
            self._processing_configuration.parser_filter_expression))

    self._extraction_worker.SetExtractionConfiguration(
        self._processing_configuration.extraction)

    self._parser_mediator.StartProfiling(
        self._processing_configuration.profiling, self._name,
        self._process_information)
    self._StartProfiling(self._processing_configuration.profiling)

    if self._analyzers_profiler:
      self._extraction_worker.SetAnalyzersProfiler(self._analyzers_profiler)

    if self._processing_profiler:
      self._extraction_worker.SetProcessingProfiler(self._processing_profiler)

    logger.debug('Worker: {0!s} (PID: {1:d}) started.'.format(
        self._name, self._pid))

    self._status = definitions.STATUS_INDICATOR_RUNNING

    try:
      logger.debug('{0!s} (PID: {1:d}) started monitoring task queue.'.format(
          self._name, self._pid))

      while not self._abort:
        try:
          task = self._task_queue.PopItem()
        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logger.debug('ConsumeItems exiting with exception: {0!s}.'.format(
              type(exception)))
          break

        if isinstance(task, plaso_queue.QueueAbort):
          logger.debug('ConsumeItems exiting, dequeued QueueAbort object.')
          break

        self._ProcessTask(task)

      logger.debug('{0!s} (PID: {1:d}) stopped monitoring task queue.'.format(
          self._name, self._pid))

    # All exceptions need to be caught here to prevent the process
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      logger.warning(
          'Unhandled exception in process: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logger.exception(exception)

      self._abort = True

    if self._analyzers_profiler:
      self._extraction_worker.SetAnalyzersProfiler(None)

    if self._processing_profiler:
      self._extraction_worker.SetProcessingProfiler(None)

    self._StopProfiling()
    self._parser_mediator.StopProfiling()

    self._extraction_worker = None
    self._file_system_cache = []
    self._parser_mediator = None
    self._resolver_context = None

    if self._abort:
      self._status = definitions.STATUS_INDICATOR_ABORTED
    else:
      self._status = definitions.STATUS_INDICATOR_COMPLETED

    logger.debug('Worker: {0!s} (PID: {1:d}) stopped.'.format(
        self._name, self._pid))

    try:
      self._task_queue.Close(abort=self._abort)
    except errors.QueueAlreadyClosed:
      logger.error('Queue for {0:s} was already closed.'.format(self.name))

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
      file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          path_spec, resolver_context=parser_mediator.resolver_context)
      if file_entry is None:
        logger.warning('Unable to open file entry: {0:s}'.format(
            self._current_display_name))
        return

      if (path_spec and not path_spec.IsSystemLevel() and
          path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_GZIP):
        file_system = file_entry.GetFileSystem()
        self._CacheFileSystem(file_system)

      extraction_worker.ProcessFileEntry(parser_mediator, file_entry)

    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning((
          'unable to process path specification with error: '
          '{0!s}').format(exception), path_spec=path_spec)

      if self._processing_configuration.debug_output:
        logger.warning((
            'Unhandled exception while processing path specification: '
            '{0:s}.').format(self._current_display_name))
        logger.exception(exception)

  def _ProcessTask(self, task):
    """Processes a task.

    Args:
      task (Task): task.
    """
    logger.debug('Started processing task: {0:s}.'.format(task.identifier))

    if self._tasks_profiler:
      self._tasks_profiler.Sample(task, 'processing_started')

    task.storage_format = self._processing_configuration.task_storage_format

    self._task = task

    task_storage_writer = self._storage_factory.CreateTaskStorageWriter(
        self._processing_configuration.task_storage_format)

    if self._serializers_profiler:
      task_storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      task_storage_writer.SetStorageProfiler(self._storage_profiler)

    self._parser_mediator.SetStorageWriter(task_storage_writer)

    storage_file_path = self._GetTaskStorageFilePath(
        self._processing_configuration.task_storage_format, task)
    task_storage_writer.Open(
        path=storage_file_path, session_identifier=task.session_identifier,
        task_identifier=task.identifier)

    try:
      task_storage_writer.AddAttributeContainer(task)

      # TODO: add support for more task types.
      self._ProcessPathSpec(
          self._extraction_worker, self._parser_mediator, task.path_spec)
      self._number_of_consumed_sources += 1

    finally:
      task.aborted = self._abort
      task_storage_writer.UpdateAttributeContainer(task)

      task_storage_writer.Close()

    self._parser_mediator.SetStorageWriter(None)

    try:
      self._FinalizeTaskStorageWriter(
          self._processing_configuration.task_storage_format, task)
    except IOError:
      pass

    self._task = None

    if self._tasks_profiler:
      self._tasks_profiler.Sample(task, 'processing_completed')

    logger.debug('Completed processing task: {0:s}.'.format(task.identifier))

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
    if self._extraction_worker:
      self._extraction_worker.SignalAbort()
    if self._parser_mediator:
      self._parser_mediator.SignalAbort()
