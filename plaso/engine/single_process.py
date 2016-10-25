# -*- coding: utf-8 -*-
"""The single process processing engine."""

import logging
import os
import pdb
import time

from dfvfs.lib import errors as dfvfs_errors

from plaso.containers import event_sources
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import profiler
from plaso.engine import worker
from plaso.lib import definitions
from plaso.parsers import mediator as parsers_mediator


class SingleProcessEngine(engine.BaseEngine):
  """Class that defines the single process engine."""

  def __init__(
      self, debug_output=False, enable_profiling=False,
      profiling_directory=None, profiling_sample_rate=1000,
      profiling_type=u'all'):
    """Initializes an engine object.

    Args:
      debug_output (Optional[bool]): True if debug output should be enabled.
      enable_profiling (Optional[bool]): True if profiling should be enabled.
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
    """
    super(SingleProcessEngine, self).__init__(
        debug_output=debug_output, enable_profiling=enable_profiling,
        profiling_directory=profiling_directory,
        profiling_sample_rate=profiling_sample_rate,
        profiling_type=profiling_type)
    self._current_display_name = u''
    self._last_status_update_timestamp = 0.0
    self._memory_profiler = None
    self._name = u'Main'
    self._parsers_profiler = None
    self._pid = os.getpid()
    self._processing_profiler = None
    self._serializers_profiler = None
    self._status_update_callback = None
    self._yara_rules_string = None

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

    except KeyboardInterrupt:
      self._abort = True

      self._processing_status.aborted = True
      if self._status_update_callback:
        self._status_update_callback(self._processing_status)

    # We cannot recover from a CacheFullError and abort processing when
    # it is raised.
    except dfvfs_errors.CacheFullError:
      # TODO: signal engine of failure.
      self._abort = True
      logging.error((
          u'ABORT: detected cache full error while processing '
          u'path spec: {0:s}').format(self._current_display_name))

    # All exceptions need to be caught here to prevent the worker
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionError((
          u'unable to process path specification with error: '
          u'{0:s}').format(exception), path_spec=path_spec)

      if self._debug_output:
        logging.warning(
            u'Unhandled exception while processing path spec: {0:s}.'.format(
                self._current_display_name))
        logging.exception(exception)

        pdb.post_mortem()

  def _ProcessSources(
      self, source_path_specs, resolver_context, extraction_worker,
      parser_mediator, storage_writer, filter_find_specs=None):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      resolver_context (dfvfs.Context): resolver context.
      extraction_worker (worker.ExtractionWorker): extraction worker.
      parser_mediator (ParserMediator): parser mediator.
      storage_writer (StorageWriter): storage writer for a session storage.
      filter_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
          used in path specification extraction.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'process_sources')

    number_of_consumed_sources = 0

    self._UpdateStatus(
        definitions.PROCESSING_STATUS_COLLECTING, u'',
        number_of_consumed_sources, storage_writer)

    path_spec_extractor = extractors.PathSpecExtractor(resolver_context)

    display_name = u''
    for path_spec in path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=filter_find_specs,
        recurse_file_system=False):
      if self._abort:
        break

      display_name = parser_mediator.GetDisplayNameForPathSpec(path_spec)

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

      self._UpdateStatus(
          definitions.PROCESSING_STATUS_COLLECTING, display_name,
          number_of_consumed_sources, storage_writer)

    # Force the status update here to make sure the status is up to date.
    self._UpdateStatus(
        definitions.PROCESSING_STATUS_RUNNING, display_name,
        number_of_consumed_sources, storage_writer, force=True)

    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'get_event_source')

    event_source = storage_writer.GetFirstWrittenEventSource()

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'get_event_source')

    while event_source:
      if self._abort:
        break

      self._ProcessPathSpec(
          extraction_worker, parser_mediator, event_source.path_spec)
      number_of_consumed_sources += 1

      if self._memory_profiler:
        self._memory_profiler.Sample()

      self._UpdateStatus(
          extraction_worker.processing_status, self._current_display_name,
          number_of_consumed_sources, storage_writer)

      if self._processing_profiler:
        self._processing_profiler.StartTiming(u'get_event_source')

      event_source = storage_writer.GetNextWrittenEventSource()

      if self._processing_profiler:
        self._processing_profiler.StopTiming(u'get_event_source')

    if self._abort:
      status = definitions.PROCESSING_STATUS_ABORTED
    else:
      status = definitions.PROCESSING_STATUS_COMPLETED

    # Force the status update here to make sure the status is up to date
    # on exit.
    self._UpdateStatus(
        status, u'', number_of_consumed_sources, storage_writer, force=True)

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'process_sources')

  def _StartProfiling(self, extraction_worker):
    """Starts profiling.

    Args:
      extraction_worker (worker.ExtractionWorker): extraction worker.
    """
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
      extraction_worker.SetParsersProfiler(self._parsers_profiler)

    if self._profiling_type in (u'all', u'processing'):
      identifier = u'{0:s}-processing'.format(self._name)
      self._processing_profiler = profiler.ProcessingProfiler(
          identifier, path=self._profiling_directory)
      extraction_worker.SetProcessingProfiler(self._processing_profiler)

    if self._profiling_type in (u'all', u'serializers'):
      identifier = u'{0:s}-serializers'.format(self._name)
      self._serializers_profiler = profiler.SerializersProfiler(
          identifier, path=self._profiling_directory)

  def _StopProfiling(self, extraction_worker):
    """Stops profiling.

    Args:
      extraction_worker (worker.ExtractionWorker): extraction worker.
    """
    if not self._enable_profiling:
      return

    if self._profiling_type in (u'all', u'memory'):
      self._memory_profiler.Sample()
      self._memory_profiler = None

    if self._profiling_type in (u'all', u'parsers'):
      extraction_worker.SetParsersProfiler(None)
      self._parsers_profiler.Write()
      self._parsers_profiler = None

    if self._profiling_type in (u'all', u'processing'):
      extraction_worker.SetProcessingProfiler(None)
      self._processing_profiler.Write()
      self._processing_profiler = None

    if self._profiling_type in (u'all', u'serializers'):
      self._serializers_profiler.Write()
      self._serializers_profiler = None

  def _UpdateStatus(
      self, status, display_name, number_of_consumed_sources, storage_writer,
      force=False):
    """Updates the processing status.

    Args:
      status (str): human readable status of the processing e.g. 'Idle'.
      display_name (str): human readable of the file entry currently being
          processed.
      number_of_consumed_sources (int): number of consumed sources.
      storage_writer (StorageWriter): storage writer for a session storage.
      force (Optional[bool]): True if the update should be forced ignoring
          the last status update time.
    """
    current_timestamp = time.time()
    if not force and current_timestamp < (
        self._last_status_update_timestamp + self._STATUS_UPDATE_INTERVAL):
      return

    if status == definitions.PROCESSING_STATUS_IDLE:
      status = definitions.PROCESSING_STATUS_RUNNING

    self._processing_status.UpdateForemanStatus(
        self._name, status, self._pid, display_name,
        number_of_consumed_sources, storage_writer.number_of_event_sources,
        0, storage_writer.number_of_events,
        0, 0,
        0, storage_writer.number_of_errors,
        0, 0)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

    self._last_status_update_timestamp = current_timestamp

  def ProcessSources(
      self, source_path_specs, storage_writer, resolver_context,
      filter_find_specs=None, filter_object=None, hasher_names_string=None,
      mount_path=None, parser_filter_expression=None, preferred_year=None,
      process_archives=False, process_compressed_streams=True,
      status_update_callback=None, temporary_directory=None,
      text_prepend=None, yara_rules_string=None):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
      resolver_context (dfvfs.Context): resolver context.
      filter_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
          used in path specification extraction.
      filter_object (Optional[objectfilter.Filter]): filter object.
      hasher_names_string (Optional[str]): comma separated string of names
          of hashers to use during processing.
      mount_path (Optional[str]): mount path.
      parser_filter_expression (Optional[str]): parser filter expression.
      preferred_year (Optional[int]): preferred year.
      process_archives (Optional[bool]): True if archive files should be
          scanned for file entries.
      process_compressed_streams (Optional[bool]): True if file content in
          compressed streams should be processed.
      status_update_callback (Optional[function]): callback function for status
          updates.
      temporary_directory (Optional[str]): path of the directory for temporary
          files.
      text_prepend (Optional[str]): text to prepend to every event.
      yara_rules_string (Optional[str]): unparsed yara rule definitions.

    Returns:
      ProcessingStatus: processing status.
    """
    parser_mediator = parsers_mediator.ParserMediator(
        storage_writer, self.knowledge_base, preferred_year=preferred_year,
        temporary_directory=temporary_directory)

    if filter_object:
      parser_mediator.SetFilterObject(filter_object)

    if mount_path:
      parser_mediator.SetMountPath(mount_path)

    if text_prepend:
      parser_mediator.SetTextPrepend(text_prepend)

    extraction_worker = worker.EventExtractionWorker(
        resolver_context, parser_filter_expression=parser_filter_expression,
        process_archives=process_archives,
        process_compressed_streams=process_compressed_streams)

    if hasher_names_string:
      extraction_worker.SetHashers(hasher_names_string)

    if yara_rules_string:
      extraction_worker.SetYaraRules(yara_rules_string)

    self._status_update_callback = status_update_callback

    logging.debug(u'Processing started.')

    self._StartProfiling(extraction_worker)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    storage_writer.Open()
    storage_writer.WriteSessionStart()

    try:
      storage_writer.WritePreprocessingInformation(self.knowledge_base)

      self._ProcessSources(
          source_path_specs, resolver_context, extraction_worker,
          parser_mediator, storage_writer, filter_find_specs=filter_find_specs)

    finally:
      storage_writer.WriteSessionCompletion(aborted=self._abort)

      storage_writer.Close()

      if self._serializers_profiler:
        storage_writer.SetSerializersProfiler(None)

      self._StopProfiling(extraction_worker)

    if self._abort:
      logging.debug(u'Processing aborted.')
      self._processing_status.aborted = True
    else:
      logging.debug(u'Processing completed.')

    self._status_update_callback = None

    return self._processing_status
