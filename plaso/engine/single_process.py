# -*- coding: utf-8 -*-
"""The single process processing engine."""

from __future__ import unicode_literals

import os
import pdb
import time

from dfvfs.lib import errors as dfvfs_errors

from plaso.containers import event_sources
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import logger
from plaso.engine import process_info
from plaso.engine import worker
from plaso.lib import definitions
from plaso.parsers import mediator as parsers_mediator


class SingleProcessEngine(engine.BaseEngine):
  """Class that defines the single process engine."""

  def __init__(self):
    """Initializes a single process engine."""
    super(SingleProcessEngine, self).__init__()
    self._current_display_name = ''
    self._last_status_update_timestamp = 0.0
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._pid = os.getpid()
    self._process_information = process_info.ProcessInfo(self._pid)
    self._processing_configuration = None
    self._status_update_callback = None

  def _ProcessPathSpec(self, extraction_worker, parser_mediator, path_spec):
    """Processes a path specification.

    Args:
      extraction_worker (worker.ExtractionWorker): extraction worker.
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
    """
    self._current_display_name = parser_mediator.GetDisplayNameForPathSpec(
        path_spec)

    excluded_find_specs = None
    if self.collection_filters_helper:
      excluded_find_specs = (
          self.collection_filters_helper.excluded_file_system_find_specs)

    try:
      extraction_worker.ProcessPathSpec(
          parser_mediator, path_spec, excluded_find_specs=excluded_find_specs)

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
      logger.error((
          'ABORT: detected cache full error while processing '
          'path spec: {0:s}').format(self._current_display_name))

    # All exceptions need to be caught here to prevent the worker
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning((
          'unable to process path specification with error: '
          '{0!s}').format(exception), path_spec=path_spec)

      if getattr(self._processing_configuration, 'debug_output', False):
        logger.warning(
            'Unhandled exception while processing path spec: {0:s}.'.format(
                self._current_display_name))
        logger.exception(exception)

        pdb.post_mortem()

  def _ProcessSources(
      self, source_path_specs, extraction_worker, parser_mediator,
      storage_writer):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      extraction_worker (worker.ExtractionWorker): extraction worker.
      parser_mediator (ParserMediator): parser mediator.
      storage_writer (StorageWriter): storage writer for a session storage.
    """
    if self._processing_profiler:
      self._processing_profiler.StartTiming('process_sources')

    number_of_consumed_sources = 0

    self._UpdateStatus(
        definitions.STATUS_INDICATOR_COLLECTING, '',
        number_of_consumed_sources, storage_writer)

    display_name = ''
    find_specs = None
    if self.collection_filters_helper:
      find_specs = (
          self.collection_filters_helper.included_file_system_find_specs)

    path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=find_specs, recurse_file_system=False,
        resolver_context=parser_mediator.resolver_context)

    for path_spec in path_spec_generator:
      if self._abort:
        break

      display_name = parser_mediator.GetDisplayNameForPathSpec(path_spec)

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

      self._UpdateStatus(
          definitions.STATUS_INDICATOR_COLLECTING, display_name,
          number_of_consumed_sources, storage_writer)

    # Force the status update here to make sure the status is up to date.
    self._UpdateStatus(
        definitions.STATUS_INDICATOR_RUNNING, display_name,
        number_of_consumed_sources, storage_writer, force=True)

    if self._processing_profiler:
      self._processing_profiler.StartTiming('get_event_source')

    event_source = storage_writer.GetFirstWrittenEventSource()

    if self._processing_profiler:
      self._processing_profiler.StopTiming('get_event_source')

    while event_source:
      if self._abort:
        break

      self._ProcessPathSpec(
          extraction_worker, parser_mediator, event_source.path_spec)
      number_of_consumed_sources += 1

      self._UpdateStatus(
          extraction_worker.processing_status, self._current_display_name,
          number_of_consumed_sources, storage_writer)

      if self._processing_profiler:
        self._processing_profiler.StartTiming('get_event_source')

      event_source = storage_writer.GetNextWrittenEventSource()

      if self._processing_profiler:
        self._processing_profiler.StopTiming('get_event_source')

    if self._abort:
      status = definitions.STATUS_INDICATOR_ABORTED
    else:
      status = definitions.STATUS_INDICATOR_COMPLETED

    # Force the status update here to make sure the status is up to date
    # on exit.
    self._UpdateStatus(
        status, '', number_of_consumed_sources, storage_writer, force=True)

    if self._processing_profiler:
      self._processing_profiler.StopTiming('process_sources')

  def _UpdateStatus(
      self, status, display_name, number_of_consumed_sources, storage_writer,
      force=False):
    """Updates the processing status.

    Args:
      status (str): human readable status indication such as "Hashing" or
          "Idle".
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

    if status == definitions.STATUS_INDICATOR_IDLE:
      status = definitions.STATUS_INDICATOR_RUNNING

    used_memory = self._process_information.GetUsedMemory() or 0

    self._processing_status.UpdateForemanStatus(
        self._name, status, self._pid, used_memory, display_name,
        number_of_consumed_sources, storage_writer.number_of_event_sources, 0,
        storage_writer.number_of_events, 0, 0, 0, 0, 0,
        storage_writer.number_of_warnings)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

    self._last_status_update_timestamp = current_timestamp

  def ProcessSources(
      self, source_path_specs, storage_writer, resolver_context,
      processing_configuration, status_update_callback=None):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      storage_writer (StorageWriter): storage writer for a session storage.
      resolver_context (dfvfs.Context): resolver context.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      status_update_callback (Optional[function]): callback function for status
          updates.

    Returns:
      ProcessingStatus: processing status.
    """
    parser_mediator = parsers_mediator.ParserMediator(
        storage_writer, self.knowledge_base,
        collection_filters_helper=self.collection_filters_helper,
        preferred_year=processing_configuration.preferred_year,
        resolver_context=resolver_context,
        temporary_directory=processing_configuration.temporary_directory)

    parser_mediator.SetEventExtractionConfiguration(
        processing_configuration.event_extraction)

    parser_mediator.SetInputSourceConfiguration(
        processing_configuration.input_source)

    extraction_worker = worker.EventExtractionWorker(
        parser_filter_expression=(
            processing_configuration.parser_filter_expression))

    extraction_worker.SetExtractionConfiguration(
        processing_configuration.extraction)

    self._processing_configuration = processing_configuration
    self._status_update_callback = status_update_callback

    logger.debug('Processing started.')

    parser_mediator.StartProfiling(
        self._processing_configuration.profiling, self._name,
        self._process_information)
    self._StartProfiling(self._processing_configuration.profiling)

    if self._processing_profiler:
      extraction_worker.SetProcessingProfiler(self._processing_profiler)

    if self._serializers_profiler:
      storage_writer.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      storage_writer.SetStorageProfiler(self._storage_profiler)

    storage_writer.Open()
    storage_writer.WriteSessionStart()

    try:
      storage_writer.WritePreprocessingInformation(self.knowledge_base)

      self._ProcessSources(
          source_path_specs, extraction_worker, parser_mediator, storage_writer)

    finally:
      storage_writer.WriteSessionCompletion(aborted=self._abort)

      storage_writer.Close()

      if self._processing_profiler:
        extraction_worker.SetProcessingProfiler(None)

      if self._serializers_profiler:
        storage_writer.SetSerializersProfiler(None)

      if self._storage_profiler:
        storage_writer.SetStorageProfiler(None)

      self._StopProfiling()
      parser_mediator.StopProfiling()

    if self._abort:
      logger.debug('Processing aborted.')
      self._processing_status.aborted = True
    else:
      logger.debug('Processing completed.')

    self._processing_configuration = None
    self._status_update_callback = None

    return self._processing_status
