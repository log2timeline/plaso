# -*- coding: utf-8 -*-
"""The single process processing engine."""

import collections
import logging
import os
# TODO: reimplement debug hook.
# import pdb
import time

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

  _STATUS_CHECK_SLEEP = 1.5

  def __init__(self):
    """Initializes the single process engine object."""
    super(SingleProcessEngine, self).__init__()
    self._last_status_update_timestamp = 0.0
    self._pid = os.getpid()
    self._status_update_callback = None

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

    Returns:
      str: processing status.
    """
    self._processing_status.UpdateForemanStatus(
        u'Main', definitions.PROCESSING_STATUS_COLLECTING, self._pid, u'',
        0, 0, 0, 0)
    self._UpdateStatus()

    path_spec_extractor = extractors.PathSpecExtractor(resolver_context)

    number_of_collected_sources = 0
    number_of_consumed_sources = 0
    for path_spec in path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=filter_find_specs,
        recurse_file_system=False):
      if self._abort:
        break

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

      number_of_collected_sources += 1

      self._processing_status.UpdateForemanStatus(
          u'Main', definitions.PROCESSING_STATUS_COLLECTING, self._pid, u'',
          number_of_consumed_sources, number_of_collected_sources, 0, 0)
      self._UpdateStatus()

    new_event_sources = True
    while new_event_sources:
      if self._abort:
        break

      # TODO: flushing the storage writer here for now to make sure the event
      # sources are written to disk. Remove this during phased processing
      # refactor.
      storage_writer.ForceFlush()

      new_event_sources = False
      for event_source in storage_writer.GetEventSources():
        new_event_sources = True
        if self._abort:
          break

        extraction_worker.ProcessPathSpec(
            parser_mediator, event_source.path_spec)
        number_of_consumed_sources += 1

        number_of_produced_sources = (
            number_of_collected_sources +
            parser_mediator.number_of_produced_event_sources)

        self._processing_status.UpdateForemanStatus(
            u'Main', definitions.PROCESSING_STATUS_EXTRACTING, self._pid,
            extraction_worker.current_display_name,
            number_of_consumed_sources, number_of_produced_sources,
            storage_writer.number_of_events,
            parser_mediator.number_of_produced_events)
        self._UpdateStatus()

    if self._abort:
      status = definitions.PROCESSING_STATUS_ABORTED
    else:
      status = definitions.PROCESSING_STATUS_COMPLETED

    number_of_produced_sources = (
        number_of_collected_sources +
        parser_mediator.number_of_produced_event_sources)

    self._processing_status.UpdateForemanStatus(
        u'Main', status, self._pid, u'',
        number_of_consumed_sources, number_of_produced_sources,
        storage_writer.number_of_events,
        parser_mediator.number_of_produced_events)
    self._UpdateStatus()

    return status

  def _UpdateStatus(self):
    """Updates the processing status."""
    current_timestamp = time.time()
    if current_timestamp < (
        self._last_status_update_timestamp + self._STATUS_CHECK_SLEEP):
      return

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

    self._last_status_update_timestamp = current_timestamp

  def ProcessSources(
      self, source_path_specs, session_start, preprocess_object,
      storage_writer, resolver_context, filter_find_specs=None,
      filter_object=None, hasher_names_string=None, mount_path=None,
      parser_filter_expression=None, process_archive_files=False,
      profiling_type=u'all', status_update_callback=None, text_prepend=None):
    """Processes the sources.

    Args:
      source_path_specs: a list of path specifications (instances of
                         dfvfs.PathSpec) of the sources to process.
      session_start: a session start attribute container (instance of
                     SessionStart).
      preprocess_object: a preprocess object (instance of PreprocessObject).
      storage_writer: a storage writer object (instance of StorageWriter).
      resolver_context: a resolver context (instance of dfvfs.Context).
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec).
      filter_object: optional filter object (instance of objectfilter.Filter).
      hasher_names_string: optional comma separated string of names of
                           hashers to enable.
      mount_path: optional string containing the mount path.
      parser_filter_expression: optional string containing the parser filter
                                expression, where None represents all parsers
                                and plugins.
      process_archive_files: optional boolean value to indicate if the worker
                             should scan for file entries inside files.
      profiling_type: optional string containing the profiling type.
      status_update_callback: optional callback function for status updates.
      text_prepend: optional string that contains the text to prepend to every
                    event object.

    Returns:
      The processing status (instance of ProcessingStatus).
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

    # TODO: differentiate between debug output and debug mode.
    extraction_worker.SetEnableDebugMode(self._enable_debug_output)

    if hasher_names_string:
      extraction_worker.SetHashers(hasher_names_string)

    if self._enable_profiling:
      extraction_worker.EnableProfiling(
          profiling_sample_rate=self._profiling_sample_rate,
          profiling_type=self._profiling_type)

    self._status_update_callback = status_update_callback

    if self._enable_profiling:
      storage_writer.EnableProfiling(profiling_type=profiling_type)

    logging.debug(u'Processing started.')

    storage_writer.Open()

    try:
      storage_writer.WriteSessionStart(session_start)

      status = self._ProcessSources(
          source_path_specs, resolver_context, extraction_worker,
          parser_mediator, storage_writer, filter_find_specs=filter_find_specs)

      # TODO: refactor the use of preprocess_object.
      storage_writer.WritePreprocessObject(preprocess_object)

    finally:
      # TODO: on abort use WriteSessionAborted instead of completion?
      storage_writer.WriteSessionCompletion()
      storage_writer.Close()

      if self._enable_profiling:
        storage_writer.DisableProfiling()

    if status == definitions.PROCESSING_STATUS_ABORTED:
      logging.debug(u'Processing aborted.')
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
