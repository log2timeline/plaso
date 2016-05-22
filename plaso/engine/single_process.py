# -*- coding: utf-8 -*-
"""The single process processing engine."""

import collections
import logging
import os
import pdb
import time

from dfvfs.resolver import context

from plaso.containers import event_sources
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import plaso_queue
from plaso.engine import worker
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator


class SingleProcessPathSpecQueueProducer(engine.PathSpecQueueProducer):
  """Class that implements a path specification queue producer object."""

  def __init__(self, path_spec_queue, storage_writer):
    """Initializes the queue producer object.

    Args:
      path_spec_queue: the path specification queue (instance of Queue).
                       This queue contains the path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      storage_writer: a storage writer object (instance of StorageWriter).
    """
    super(SingleProcessPathSpecQueueProducer, self).__init__(
        path_spec_queue, storage_writer)
    self._extraction_worker = None

  def _FlushQueue(self):
    """Flushes the queue, callback for the QueueFull exception."""
    self._UpdateStatus()
    while not self._queue.IsEmpty():
      self._extraction_worker.Run()

  def _UpdateStatus(self):
    """Updates the processing status."""
    # Set the status to waiting while emptying the queue.
    self._status = definitions.PROCESSING_STATUS_WAITING

  def SetExtractionWorker(self, extraction_worker):
    """Sets the extraction worker.

    Args:
      extraction_worker: the extraction worker object (instance of
                         EventExtractionWorker).
    """
    self._extraction_worker = extraction_worker


class SingleProcessEngine(engine.BaseEngine):
  """Class that defines the single process engine."""

  _STATUS_CHECK_SLEEP = 1.5

  def __init__(self, maximum_number_of_queued_items=0):
    """Initialize the single process engine object.

    Args:
      maximum_number_of_queued_items: the maximum number of queued items.
                                      The default is 0, which represents
                                      no limit.
    """
    path_spec_queue = SingleProcessQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)
    event_object_queue = SingleProcessQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)
    parse_error_queue = SingleProcessQueue(
        maximum_number_of_queued_items=maximum_number_of_queued_items)

    super(SingleProcessEngine, self).__init__(
        path_spec_queue, event_object_queue, parse_error_queue)

    self._extraction_worker = None
    self._event_queue_producer = SingleProcessItemQueueProducer(
        event_object_queue)
    self._event_object_consumer = None
    self._last_status_update_timestamp = time.time()
    self._parse_error_queue_producer = SingleProcessItemQueueProducer(
        parse_error_queue)
    self._path_spec_producer = None
    self._status_update_callback = None

  def _CreateExtractionWorker(
      self, worker_number, filter_object=None, mount_path=None,
      process_archive_files=False, text_prepend=None):
    """Creates an extraction worker object.

    Args:
      worker_number: a number that identifies the worker.
      filter_object: optional filter object (instance of objectfilter.Filter).
      mount_path: optional string containing the mount path.
      process_archive_files: optional boolean value to indicate if the worker
                             should scan for file entries inside files.
      text_prepend: optional string that contains the text to prepend to every
                    event object.

    Returns:
      An extraction worker (instance of worker.ExtractionWorker).
    """
    parser_mediator = parsers_mediator.ParserMediator(
        self._event_queue_producer, self._parse_error_queue_producer,
        self.knowledge_base)

    resolver_context = context.Context()

    extraction_worker = SingleProcessEventExtractionWorker(
        worker_number, self._path_spec_queue, self._event_queue_producer,
        self._parse_error_queue_producer, parser_mediator,
        resolver_context=resolver_context,
        status_update_callback=self._UpdateStatus)

    # TODO: differentiate between debug output and debug mode.
    extraction_worker.SetEnableDebugMode(self._enable_debug_output)

    extraction_worker.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type)

    extraction_worker.SetProcessArchiveFiles(process_archive_files)

    if filter_object:
      extraction_worker.SetFilterObject(filter_object)

    if mount_path:
      extraction_worker.SetMountPath(mount_path)

    if text_prepend:
      extraction_worker.SetTextPrepend(text_prepend)

    return extraction_worker

  def _UpdateCollectorStatus(self, processing_completed=False):
    """Updates the collector status.

    Args:
      processing_completed: optional boolean value the processing has been
                            completed.
    """
    status = self._path_spec_producer.GetStatus()
    status_indicator = status.get(u'processing_status', None)
    produced_number_of_path_specs = status.get(
        u'produced_number_of_path_specs', 0)

    if processing_completed:
      status_indicator = definitions.PROCESSING_STATUS_COMPLETED
    elif status_indicator == definitions.PROCESSING_STATUS_INITIALIZED:
      status_indicator = definitions.PROCESSING_STATUS_RUNNING

    self._processing_status.UpdateCollectorStatus(
        u'Collector', os.getpid(), produced_number_of_path_specs,
        status_indicator, None)

  def _UpdateExtractionWorkerStatus(self, processing_completed=False):
    """Updates the extraction worker status.

    Args:
      processing_completed: optional boolean value the processing has been
                            completed.
    """
    status = self._extraction_worker.GetStatus()
    status_indicator = status.get(u'processing_status', None)
    consumed_number_of_path_specs = status.get(
        u'consumed_number_of_path_specs', 0)
    display_name = status.get(u'display_name', u'')
    number_of_events = status.get(u'number_of_events', 0)
    produced_number_of_path_specs = status.get(
        u'produced_number_of_path_specs', 0)

    if processing_completed:
      status_indicator = definitions.PROCESSING_STATUS_COMPLETED
    elif status_indicator in (
        definitions.PROCESSING_STATUS_COMPLETED,
        definitions.PROCESSING_STATUS_INITIALIZED):
      # If the worker is initialized or completed in single
      # processing mode it is actually waiting for input.
      status_indicator = definitions.PROCESSING_STATUS_WAITING

    self._processing_status.UpdateExtractionWorkerStatus(
        u'Worker', os.getpid(), display_name, number_of_events,
        consumed_number_of_path_specs, produced_number_of_path_specs,
        status_indicator, None)

  def _UpdateStorageWriterStatus(self, processing_completed=False):
    """Updates the storage writer status.

    Args:
      processing_completed: optional boolean value the processing has been
                            completed.
    """
    status = self._event_object_consumer.GetStatus()
    status_indicator = status.get(u'processing_status', None)
    number_of_events = status.get(u'number_of_events', 0)

    if processing_completed:
      status_indicator = definitions.PROCESSING_STATUS_COMPLETED
    elif status_indicator in (
        definitions.PROCESSING_STATUS_COMPLETED,
        definitions.PROCESSING_STATUS_INITIALIZED):
      # If the storage writer is initialized or completed in single
      # processing mode it is actually waiting for input.
      status_indicator = definitions.PROCESSING_STATUS_WAITING

    self._processing_status.UpdateStorageWriterStatus(
        u'StorageWriter', os.getpid(), number_of_events, status_indicator, None)

  def _UpdateStatus(self, processing_completed=False):
    """Updates the processing status.

    Args:
      processing_completed: optional boolean value the processing has been
                            completed.
    """
    current_timestamp = time.time()
    if current_timestamp < (
        self._last_status_update_timestamp + self._STATUS_CHECK_SLEEP):
      return

    self._UpdateCollectorStatus(processing_completed=processing_completed)
    self._UpdateExtractionWorkerStatus(
        processing_completed=processing_completed)
    self._UpdateStorageWriterStatus(processing_completed=processing_completed)

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

    self._last_status_update_timestamp = current_timestamp

  def _ExtractEventSources(
      self, source_path_specs, storage_writer, filter_find_specs=None,
      resolver_context=None):
    """Processes the sources and extract event sources.

    Args:
      source_path_specs: a list of path specifications (instances of
                         dfvfs.PathSpec) of the sources to process.
      resolver_context: resolver context (instance of dfvfs.Context).
      storage_writer: a storage writer object (instance of StorageWriter).
      filter_find_specs: optional list of filter find specifications (instances
                         of dfvfs.FindSpec).
    """
    path_spec_extractor = extractors.PathSpecExtractor(resolver_context)

    for path_spec in path_spec_extractor.ExtractPathSpecs(
        source_path_specs, find_specs=filter_find_specs):

      # TODO: determine if event sources should be DataStream or FileEntry
      # or both.
      event_source = event_sources.FileEntryEventSource(path_spec=path_spec)
      storage_writer.AddEventSource(event_source)

  def ProcessSources(
      self, source_path_specs, storage_writer, filter_find_specs=None,
      filter_object=None, hasher_names_string=None, mount_path=None,
      parser_filter_expression=None, process_archive_files=False,
      resolver_context=None, status_update_callback=None, text_prepend=None):
    """Processes the sources and extract event objects.

    Args:
      source_path_specs: a list of path specifications (instances of
                         dfvfs.PathSpec) of the sources to process.
      storage_writer: a storage writer object (instance of StorageWriter).
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
      resolver_context: optional resolver context (instance of dfvfs.Context).
      status_update_callback: optional callback function for status updates.
      text_prepend: optional string that contains the text to prepend to every
                    event object.

    Returns:
      The processing status (instance of ProcessingStatus).
    """
    logging.debug(u'Processing started.')

    self._status_update_callback = status_update_callback

    # TODO: pass status update callback.
    self._ExtractEventSources(
        source_path_specs, storage_writer, filter_find_specs=filter_find_specs,
        resolver_context=resolver_context)

    # TODO: flushing the storage writer here for now to make sure the event
    # sources are written to disk. Remove this during phased processing
    # refactor.
    storage_writer.ForceFlush()

    self._path_spec_producer = SingleProcessPathSpecQueueProducer(
        self._path_spec_queue, storage_writer)

    self._extraction_worker = self._CreateExtractionWorker(
        0, filter_object=filter_object, mount_path=mount_path,
        process_archive_files=process_archive_files,
        text_prepend=text_prepend)

    if hasher_names_string:
      self._extraction_worker.SetHashers(hasher_names_string)

    self._extraction_worker.InitializeParserObjects(
        parser_filter_expression=parser_filter_expression)

    self._event_object_consumer = engine.EventObjectQueueConsumer(
        self._event_object_queue, storage_writer)

    # Set the extraction worker and storage writer values so that they
    # can be accessed if the QueueFull exception is raised. This is
    # needed in single process mode to prevent the queue consuming too
    # much memory.
    self._path_spec_producer.SetExtractionWorker(self._extraction_worker)
    self._event_queue_producer.SetEventObjectConsumer(
        self._event_object_consumer)
    self._parse_error_queue_producer.SetEventObjectConsumer(
        self._event_object_consumer)

    self._UpdateStatus()
    # TODO: remove queues.
    self._path_spec_producer.Run()

    self._UpdateStatus()
    # TODO: split hashing and extraction phases.
    self._extraction_worker.Run()

    self._UpdateStatus()
    self._event_object_consumer.Run()

    self._UpdateStatus(processing_completed=True)

    storage_writer.WriteSessionCompletion()
    storage_writer.Close()

    # Reset the extraction worker and storage writer values to return
    # the objects in their original state. This will prevent access
    # to the extraction worker outside this function and allow it
    # to be garbage collected.
    self._extraction_worker = None
    self._event_object_consumer = None
    self._event_queue_producer.SetEventObjectConsumer(None)
    self._parse_error_queue_producer.SetEventObjectConsumer(None)
    self._path_spec_producer = None
    self._status_update_callback = None

    logging.debug(u'Processing completed.')

    return self._processing_status

  def SignalAbort(self):
    """Signals the engine to abort."""
    self._event_queue_producer.SignalAbort()
    self._parse_error_queue_producer.SignalAbort()

    if self._path_spec_producer:
      self._path_spec_producer.SignalAbort()


class SingleProcessEventExtractionWorker(worker.BaseEventExtractionWorker):
  """Class that defines the single process event extraction worker."""

  def __init__(
      self, identifier, path_spec_queue, event_queue_producer,
      parse_error_queue_producer, parser_mediator, resolver_context=None,
      status_update_callback=None):
    """Initializes the event extraction worker object.

    Args:
      identifier: the identifier, usually an incrementing integer.
      path_spec_queue: the path specification queue (instance of Queue).
                       This queue contains the path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      event_queue_producer: the event object queue producer (instance of
                            ItemQueueProducer).
      parse_error_queue_producer: the parse error queue producer (instance of
                                  ItemQueueProducer).
      parser_mediator: a parser mediator object (instance of ParserMediator).
      resolver_context: optional resolver context (instance of dfvfs.Context).
      status_update_callback: optional callback function for status updates.
    """
    super(SingleProcessEventExtractionWorker, self).__init__(
        identifier, path_spec_queue, event_queue_producer,
        parse_error_queue_producer, parser_mediator,
        resolver_context=resolver_context)

    self._status_update_callback = status_update_callback

  def _ConsumeItem(self, path_spec, **kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).

    Raises:
      QueueFull: If a queue is full.
    """
    if self._status_update_callback:
      self._status_update_callback()

    super(SingleProcessEventExtractionWorker, self)._ConsumeItem(
        path_spec, **kwargs)

  def _DebugProcessPathSpec(self):
    """Callback for debugging path specification processing failures."""
    pdb.post_mortem()


class SingleProcessItemQueueProducer(plaso_queue.ItemQueueProducer):
  """Class that implements a single process item queue producer."""

  def __init__(self, queue_object):
    """Initializes the queue producer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(SingleProcessItemQueueProducer, self).__init__(queue_object)
    self._event_object_consumer = None

  def _FlushQueue(self):
    """Flushes the queue callback for the QueueFull exception."""
    self._event_object_consumer.Run()

  def SetEventObjectConsumer(self, event_object_consumer):
    """Sets the event object queue consumer.

    Args:
      event_object_consumer: an event object queue consumer (instance of
                             ItemQueueConsumer).
    """
    self._event_object_consumer = event_object_consumer


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
