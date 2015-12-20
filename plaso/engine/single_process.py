# -*- coding: utf-8 -*-
"""The single process processing engine."""

import collections
import logging
import pdb

from dfvfs.resolver import context

from plaso.engine import collector
from plaso.engine import engine
from plaso.engine import queue
from plaso.engine import worker
from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator


class SingleProcessCollector(collector.Collector):
  """Class that implements a single process collector object."""

  def __init__(self, path_spec_queue, resolver_context=None):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      path_spec_queue: The path specification queue (instance of Queue).
                       This queue contains the path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None.
    """
    super(SingleProcessCollector, self).__init__(
        path_spec_queue, resolver_context=resolver_context)

    self._extraction_worker = None
    self._fs_collector = SingleProcessFileSystemCollector(path_spec_queue)

  def _FlushQueue(self):
    """Flushes the queue callback for the QueueFull exception."""
    while not self._queue.IsEmpty():
      logging.debug(u'Extraction worker started.')
      self._extraction_worker.Run()
      logging.debug(u'Extraction worker stopped.')

  def SetExtractionWorker(self, extraction_worker):
    """Sets the extraction worker.

    Args:
      extraction_worker: the extraction worker object (instance of
                         EventExtractionWorker).
    """
    self._extraction_worker = extraction_worker

    self._fs_collector.SetExtractionWorker(extraction_worker)


class SingleProcessEngine(engine.BaseEngine):
  """Class that defines the single process engine."""

  def __init__(self, maximum_number_of_queued_items=0):
    """Initialize the single process engine object.

    Args:
      maximum_number_of_queued_items: The maximum number of queued items.
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

    self._collector = None
    self._event_queue_producer = SingleProcessItemQueueProducer(
        event_object_queue)
    self._parse_error_queue_producer = SingleProcessItemQueueProducer(
        parse_error_queue)

  def _CreateCollector(
      self, filter_find_specs=None, include_directory_stat=True,
      resolver_context=None):
    """Creates a collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      include_directory_stat: Optional boolean value to indicate whether
                              directory stat information should be collected.
                              The default is True.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      A collector object (instance of Collector).
    """
    collector_object = SingleProcessCollector(
        self._path_spec_queue, resolver_context=resolver_context)

    collector_object.SetCollectDirectoryMetadata(include_directory_stat)

    if filter_find_specs:
      collector_object.SetFilter(filter_find_specs)

    return collector_object

  def _CreateExtractionWorker(
      self, worker_number, filter_object=None, mount_path=None,
      process_archive_files=False, text_prepend=None):
    """Creates an extraction worker object.

    Args:
      worker_number: A number that identifies the worker.
      filter_object: Optional filter object (instance of objectfilter.Filter).
                     The default is None.
      mount_path: Optional string containing the mount path. The default
                  is None.
      process_archive_files: Optional boolean value to indicate if the worker
                             should scan for file entries inside files.
                             The default is False.
      text_prepend: Optional string that contains the text to prepend to every
                    event object. The default is None.

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
        resolver_context=resolver_context)

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

  def ProcessSources(
      self, source_path_specs, storage_writer, filter_find_specs=None,
      filter_object=None, hasher_names_string=None, include_directory_stat=True,
      mount_path=None, parser_filter_string=None, process_archive_files=False,
      resolver_context=None, status_update_callback=None, text_prepend=None):
    """Processes the sources and extract event objects.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      storage_writer: A storage writer object (instance of BaseStorageWriter).
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      filter_object: Optional filter object (instance of objectfilter.Filter).
                     The default is None.
      hasher_names_string: Optional comma separated string of names of
                           hashers to enable. The default is None.
      include_directory_stat: Optional boolean value to indicate whether
                              directory stat information should be collected.
                              The default is True.
      mount_path: Optional string containing the mount path. The default
                  is None.
      parser_filter_string: Optional parser filter string. The default is None.
      process_archive_files: Optional boolean value to indicate if the worker
                             should scan for file entries inside files.
                             The default is False.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.
      status_update_callback: Optional callback function for status updates.
                              The default is None.
      text_prepend: Optional string that contains the text to prepend to every
                    event object. The default is None.

    Returns:
      The processing status (instance of ProcessingStatus).
    """
    self._collector = self._CreateCollector(
        filter_find_specs=filter_find_specs,
        include_directory_stat=include_directory_stat,
        resolver_context=resolver_context)

    extraction_worker = self._CreateExtractionWorker(
        0, filter_object=filter_object, mount_path=mount_path,
        process_archive_files=process_archive_files, text_prepend=text_prepend)

    if hasher_names_string:
      extraction_worker.SetHashers(hasher_names_string)

    extraction_worker.InitializeParserObjects(
        parser_filter_string=parser_filter_string)

    # Set the extraction worker and storage writer values so that they
    # can be accessed if the QueueFull exception is raised. This is
    # needed in single process mode to prevent the queue consuming too
    # much memory.
    self._collector.SetExtractionWorker(extraction_worker)
    self._event_queue_producer.SetStorageWriter(storage_writer)
    self._parse_error_queue_producer.SetStorageWriter(storage_writer)

    # TODO: implement using status_update_callback.
    _ = status_update_callback

    logging.debug(u'Processing started.')

    logging.debug(u'Collection started.')
    self._collector.Collect(source_path_specs)
    logging.debug(u'Collection stopped.')

    logging.debug(u'Extraction worker started.')
    extraction_worker.Run()
    logging.debug(u'Extraction worker stopped.')

    logging.debug(u'Storage writer started.')
    storage_writer.WriteEventObjects()
    logging.debug(u'Storage writer stopped.')

    # Reset the extraction worker and storage writer values to return
    # the objects in their original state. This will prevent access
    # to the extraction worker outside this function and allow it
    # to be garbage collected.
    self._event_queue_producer.SetStorageWriter(None)
    self._parse_error_queue_producer.SetStorageWriter(None)
    self._collector = None

    logging.debug(u'Processing completed.')

    return self._processing_status

  def SignalAbort(self):
    """Signals the engine to abort."""
    self._event_queue_producer.SignalAbort()
    self._parse_error_queue_producer.SignalAbort()

    if self._collector:
      self._collector.SignalAbort()


class SingleProcessEventExtractionWorker(worker.BaseEventExtractionWorker):
  """Class that defines the single process event extraction worker."""

  def _DebugProcessPathSpec(self):
    """Callback for debugging path specification processing failures."""
    pdb.post_mortem()


class SingleProcessFileSystemCollector(collector.FileSystemCollector):
  """Class that implements a single process file system collector object."""

  def __init__(self, path_spec_queue):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      path_spec_queue: The path specification queue (instance of Queue).
                       This queue contains the path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
    """
    super(SingleProcessFileSystemCollector, self).__init__(path_spec_queue)

    self._extraction_worker = None

  def _FlushQueue(self):
    """Flushes the queue callback for the QueueFull exception."""
    while not self._queue.IsEmpty():
      logging.debug(u'Extraction worker started.')
      self._extraction_worker.Run()
      logging.debug(u'Extraction worker stopped.')

  def SetExtractionWorker(self, extraction_worker):
    """Sets the extraction worker.

    Args:
      extraction_worker: the extraction worker object (instance of
                         EventExtractionWorker).
    """
    self._extraction_worker = extraction_worker


class SingleProcessItemQueueProducer(queue.ItemQueueProducer):
  """Class that implements a single process item queue producer."""

  def __init__(self, queue_object):
    """Initializes the queue producer.

    Args:
      queue_object: the queue object (instance of Queue).
    """
    super(SingleProcessItemQueueProducer, self).__init__(queue_object)

    self._storage_writer = None

  def _FlushQueue(self):
    """Flushes the queue callback for the QueueFull exception."""
    logging.debug(u'Storage writer started.')
    self._storage_writer.WriteEventObjects()
    logging.debug(u'Storage writer stopped.')

  def SetStorageWriter(self, storage_writer):
    """Sets the storage writer.

    Args:
      storage_writer: the storage writer object (instance of
                      BaseStorageWriter).
    """
    self._storage_writer = storage_writer


class SingleProcessQueue(queue.Queue):
  """Single process queue."""

  def __init__(self, maximum_number_of_queued_items=0):
    """Initializes a single process queue object.

    Args:
      maximum_number_of_queued_items: The maximum number of queued items.
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
