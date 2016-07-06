# -*- coding: utf-8 -*-
"""The single process processing engine."""

import collections
import logging
import os
import pdb
import time

from dfvfs.lib import errors as dfvfs_errors

from plaso.containers import event_sources
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import plaso_queue
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator


class SingleProcessEngine(engine.BaseEngine):
  """Class that defines the single process engine."""

  def __init__(self):
    """Initializes the single process engine object."""
    super(SingleProcessEngine, self).__init__()
    self._last_status_update_timestamp = 0.0
    self._pid = os.getpid()
    self._status_update_callback = None

  def _ProcessPathSpec(self, extraction_worker, parser_mediator, path_spec):
    """Processes a path specification.

    Args:
      extraction_worker (worker.ExtractionWorker): extraction worker.
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
    """
    try:
      extraction_worker.ProcessPathSpec(parser_mediator, path_spec)

    except KeyboardInterrupt:
      self.SignalAbort()

    except IOError as exception:
      logging.warning(
          u'Unable to process path spec: {0:s} with error: {1:s}'.format(
              extraction_worker.current_display_name, exception))

    except dfvfs_errors.CacheFullError:
      # TODO: signal engine of failure.
      self._abort = True
      logging.error((
          u'ABORT: detected cache full error while processing '
          u'path spec: {0:s}').format(
              extraction_worker.current_display_name))

    # All exceptions need to be caught here to prevent the worker
    # from being killed by an uncaught exception.
    except Exception as exception:  # pylint: disable=broad-except
      logging.warning(
          u'Unhandled exception while processing path spec: {0:s}.'.format(
              extraction_worker.current_display_name))
      logging.exception(exception)

      if self._enable_debug_output:
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
    display_name = u''
    number_of_consumed_sources = 0

    self._processing_status.UpdateForemanStatus(
        u'Main', definitions.PROCESSING_STATUS_COLLECTING, self._pid,
        display_name, number_of_consumed_sources,
        storage_writer.number_of_event_sources, 0,
        storage_writer.number_of_events)
    self._UpdateStatus()

    path_spec_extractor = extractors.PathSpecExtractor(resolver_context)

    for path_spec in path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=filter_find_specs,
        recurse_file_system=False):
      if self._abort:
        break

      display_name = parser_mediator.GetDisplayNameFromPathSpec(path_spec)

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

      self._processing_status.UpdateForemanStatus(
          u'Main', definitions.PROCESSING_STATUS_COLLECTING, self._pid,
          display_name, number_of_consumed_sources,
          storage_writer.number_of_event_sources, 0,
          storage_writer.number_of_events)
      self._UpdateStatus()

    self._processing_status.UpdateForemanStatus(
        u'Main', definitions.PROCESSING_STATUS_RUNNING, self._pid,
        display_name, number_of_consumed_sources,
        storage_writer.number_of_event_sources, 0,
        storage_writer.number_of_events)

    # Force the status update here to make sure the status is up to date.
    self._UpdateStatus(force=True)

    new_event_sources = True
    while new_event_sources:
      if self._abort:
        break

      new_event_sources = False
      event_source = storage_writer.GetNextEventSource()
      while event_source:
        new_event_sources = True
        if self._abort:
          break

        self._ProcessPathSpec(
            extraction_worker, parser_mediator, event_source.path_spec)
        number_of_consumed_sources += 1

        event_source = storage_writer.GetNextEventSource()

        processing_status = extraction_worker.processing_status
        if processing_status == definitions.PROCESSING_STATUS_IDLE:
          processing_status = definitions.PROCESSING_STATUS_RUNNING

        self._processing_status.UpdateForemanStatus(
            u'Main', processing_status, self._pid,
            extraction_worker.current_display_name,
            number_of_consumed_sources, storage_writer.number_of_event_sources,
            0, storage_writer.number_of_events)
        self._UpdateStatus()

    if self._abort:
      status = definitions.PROCESSING_STATUS_ABORTED
    else:
      status = definitions.PROCESSING_STATUS_COMPLETED

    self._processing_status.UpdateForemanStatus(
        u'Main', status, self._pid, u'',
        number_of_consumed_sources, storage_writer.number_of_event_sources,
        0, storage_writer.number_of_events)

    # Force the status update here to make sure the status is up to date
    # on exit.
    self._UpdateStatus(force=True)

  def _UpdateStatus(self, force=False):
    """Updates the processing status.

    Args:
      force (Optional[bool]): True if the update should be forced ignoring
                              the last status update time.
    """
    current_timestamp = time.time()
    if not force and current_timestamp < (
        self._last_status_update_timestamp + self._STATUS_UPDATE_INTERVAL):
      return

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

    self._last_status_update_timestamp = current_timestamp

  def ProcessSources(
      self, source_path_specs, preprocess_object, storage_writer,
      resolver_context, filter_find_specs=None, filter_object=None,
      hasher_names_string=None, mount_path=None, parser_filter_expression=None,
      process_archive_files=False, profiling_type=u'all',
      status_update_callback=None, text_prepend=None):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      preprocess_object (PreprocessObject): preprocess object.
      storage_writer (StorageWriter): storage writer for a session storage.
      resolver_context (dfvfs.Context): resolver context.
      filter_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
          used in path specification extraction.
      filter_object (Optional[objectfilter.Filter]): filter object.
      hasher_names_string (Optional[str]): comma separated string of names
                                           of hashers to use during processing.
      mount_path (Optional[str]): mount path.
      parser_filter_expression (Optional[str]): parser filter expression.
      process_archive_files (Optional[bool]): True if archive files should be
                                              scanned for file entries.
      profiling_type (Optional[str]): profiling type.
      status_update_callback (Optional[function]): callback function for status
                                                   updates.
      text_prepend (Optional[str]): text to prepend to every event.

    Returns:
      ProcessingStatus: processing status.
    """
    parser_mediator = parsers_mediator.ParserMediator(
        storage_writer, self.knowledge_base)

    if filter_object:
      parser_mediator.SetFilterObject(filter_object)

    if mount_path:
      parser_mediator.SetMountPath(mount_path)

    if text_prepend:
      parser_mediator.SetTextPrepend(text_prepend)

    extraction_worker = worker.EventExtractionWorker(
        resolver_context, parser_filter_expression=parser_filter_expression,
        process_archive_files=process_archive_files)

    if hasher_names_string:
      extraction_worker.SetHashers(hasher_names_string)

    if self._enable_profiling:
      extraction_worker.EnableProfiling(
          profiling_sample_rate=self._profiling_sample_rate,
          profiling_type=self._profiling_type)

    self._status_update_callback = status_update_callback

    logging.debug(u'Processing started.')

    if self._enable_profiling:
      storage_writer.EnableProfiling(profiling_type=profiling_type)

    storage_writer.Open()

    try:
      storage_writer.WriteSessionStart()

      self._ProcessSources(
          source_path_specs, resolver_context, extraction_worker,
          parser_mediator, storage_writer, filter_find_specs=filter_find_specs)

      # TODO: refactor the use of preprocess_object.
      storage_writer.WritePreprocessObject(preprocess_object)

      # TODO: on abort use WriteSessionAborted instead of completion?
      storage_writer.WriteSessionCompletion()

    finally:
      if self._enable_profiling:
        storage_writer.DisableProfiling()

    if self._abort:
      logging.debug(u'Processing aborted.')
      self._processing_status.aborted = True
    else:
      logging.debug(u'Processing completed.')

    self._status_update_callback = None

    return self._processing_status


class SingleProcessQueue(plaso_queue.Queue):
  """Single process queue."""

  def __init__(self, maximum_number_of_queued_items=0):
    """Initializes a single process queue object.

    Args:
      maximum_number_of_queued_items: the maximum number of queued items.
                                      The default is 0, which represents
                                      no limit.
    """
    super(SingleProcessQueue, self).__init__()

    # The Queue interface defines the maximum number of queued items to be
    # 0 if unlimited as does the multi processing queue, but deque uses
    # None to indicate no limit.
    if maximum_number_of_queued_items == 0:
      maximum_number_of_queued_items = None

    # maxlen contains the maximum number of items allowed to be queued,
    # where None represents unlimited.
    self._queue = collections.deque(
        maxlen=maximum_number_of_queued_items)

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return len(self._queue) == 0

  def PushItem(self, item):
    """Pushes an item onto the queue.

    Raises:
      QueueFull: when the queue is full.
    """
    number_of_items = len(self._queue)

    # Deque will drop the first item in the queue when maxlen is exceeded.
    if not self._queue.maxlen or number_of_items < self._queue.maxlen:
      self._queue.append(item)
      number_of_items += 1

    if self._queue.maxlen and number_of_items == self._queue.maxlen:
      raise errors.QueueFull

  def PopItem(self):
    """Pops an item off the queue or None on timeout.

    Raises:
      QueueClose: on user abort.
      QueueEmpty: when the queue is empty.
    """
    try:
      # Using popleft to have FIFO behavior.
      return self._queue.popleft()
    except IndexError:
      raise errors.QueueEmpty
    except KeyboardInterrupt:
      raise errors.QueueClose

  def Close(self):
    """Closes this queue, indicating that no further items will be added to it.

    This method has no effect on for the single process queue, but is included
    for compatibility with the Multiprocessing queue."""
    return

  def Open(self):
    """Opens the queue, ready to enqueue or dequeue items.

    This method has no effect on for the single process queue, but is included
    for compatibility with the Multiprocessing queue."""
    return
