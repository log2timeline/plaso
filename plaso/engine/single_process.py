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

  def __init__(
      self, path_spec_queue, source_path, source_path_spec,
      resolver_context=None):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      path_spec_queue: The path specification queue (instance of Queue).
                       This queue contains the path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      source_path: Path of the source file or directory.
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None.
    """
    super(SingleProcessCollector, self).__init__(
        path_spec_queue, source_path, source_path_spec,
        resolver_context=resolver_context)

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

    self._event_queue_producer = SingleProcessItemQueueProducer(
        event_object_queue)
    self._parse_error_queue_producer = SingleProcessItemQueueProducer(
        parse_error_queue)

  def CreateCollector(
      self, include_directory_stat, vss_stores=None, filter_find_specs=None,
      resolver_context=None):
    """Creates a collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected.
      vss_stores: Optional list of VSS stores to include in the collection,
                  where 1 represents the first store. Set to None if no
                  VSS stores should be processed. The default is None.
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      A collector object (instance of Collector).

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_path_spec:
      raise RuntimeError(u'Missing source.')

    collector_object = SingleProcessCollector(
        self._path_spec_queue, self._source, self._source_path_spec,
        resolver_context=resolver_context)

    collector_object.SetCollectDirectoryMetadata(include_directory_stat)

    if vss_stores:
      collector_object.SetVssInformation(vss_stores)

    if filter_find_specs:
      collector_object.SetFilter(filter_find_specs)

    return collector_object

  def CreateExtractionWorker(self, worker_number):
    """Creates an extraction worker object.

    Args:
      worker_number: A number that identifies the worker.

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

    extraction_worker.SetEnableDebugOutput(self._enable_debug_output)

    extraction_worker.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type)

    if self._process_archive_files:
      extraction_worker.SetProcessArchiveFiles(self._process_archive_files)

    if self._filter_object:
      extraction_worker.SetFilterObject(self._filter_object)

    if self._mount_path:
      extraction_worker.SetMountPath(self._mount_path)

    if self._text_prepend:
      extraction_worker.SetTextPrepend(self._text_prepend)

    return extraction_worker

  def ProcessSource(
      self, collector_object, storage_writer, hasher_names_string=None,
      parser_filter_string=None):
    """Processes the source and extracts event objects.

    Args:
      collector_object: A collector object (instance of Collector).
      storage_writer: A storage writer object (instance of BaseStorageWriter).
      hasher_names_string: Optional comma separated string of names of
                           hashers to enable. The default is None.
      parser_filter_string: Optional parser filter string. The default is None.
    """
    extraction_worker = self.CreateExtractionWorker(0)

    if hasher_names_string:
      extraction_worker.SetHashers(hasher_names_string)

    extraction_worker.InitializeParserObjects(
        parser_filter_string=parser_filter_string)

    # Set the extraction worker and storage writer values so that they
    # can be accessed if the QueueFull exception is raised. This is
    # needed in single process mode to prevent the queue consuming too
    # much memory.
    collector_object.SetExtractionWorker(extraction_worker)
    self._event_queue_producer.SetStorageWriter(storage_writer)
    self._parse_error_queue_producer.SetStorageWriter(storage_writer)

    logging.debug(u'Processing started.')

    logging.debug(u'Collection started.')
    collector_object.Collect()
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
    collector_object.SetExtractionWorker(None)

    logging.debug(u'Processing completed.')


class SingleProcessEventExtractionWorker(worker.BaseEventExtractionWorker):
  """Class that defines the single process event extraction worker."""

  def _DebugParseFileEntry(self):
    """Callback for debugging file entry parsing failures."""
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
    pass
