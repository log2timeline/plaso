# -*- coding: utf-8 -*-
"""The processing engine."""

import abc
import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import collector
from plaso.engine import knowledge_base
from plaso.engine import profiler
from plaso.engine import queue
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager


class BaseEngine(object):
  """Class that defines the processing engine base."""

  def __init__(self, path_spec_queue, event_object_queue, parse_error_queue):
    """Initialize the engine object.

    Args:
      path_spec_queue: the path specification queue object (instance of Queue).
      event_object_queue: the event object queue object (instance of Queue).
      parse_error_queue: the parser error queue object (instance of Queue).
    """
    self._enable_debug_output = False
    self._enable_profiling = False
    self._event_queue_producer = queue.ItemQueueProducer(event_object_queue)
    self._filter_object = None
    self._mount_path = None
    self._path_spec_queue = path_spec_queue
    self._parse_error_queue = parse_error_queue
    self._parse_error_queue_producer = queue.ItemQueueProducer(
        parse_error_queue)
    self._process_archive_files = False
    self._profiling_sample_rate = 1000
    self._profiling_type = u'all'
    self._text_prepend = None

    self.event_object_queue = event_object_queue
    self.knowledge_base = knowledge_base.KnowledgeBase()

  def CreateCollector(
      self, include_directory_stat, filter_find_specs=None,
      resolver_context=None):
    """Creates a collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected.
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      A collector object (instance of Collector).
    """
    collector_object = collector.Collector(
        self._path_spec_queue, resolver_context=resolver_context)

    collector_object.SetCollectDirectoryMetadata(include_directory_stat)

    if filter_find_specs:
      collector_object.SetFilter(filter_find_specs)

    return collector_object

  @abc.abstractmethod
  def CreateExtractionWorker(self, worker_number):
    """Creates an extraction worker object.

    Args:
      worker_number: A number that identifies the worker.

    Returns:
      An extraction worker (instance of worker.ExtractionWorker).
    """

  def GetSourceFileSystemSearcher(
      self, source_path_spec, resolver_context=None):
    """Retrieves the file system searcher of the source.

    Args:
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) of the file system.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      A tuple of the file system (instance of dfvfs.FileSystem) and
      the file system searcher object (instance of dfvfs.FileSystemSearcher).

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not source_path_spec:
      raise RuntimeError(u'Missing source.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        source_path_spec, resolver_context=resolver_context)

    type_indicator = source_path_spec.type_indicator
    if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
      mount_point = source_path_spec
    else:
      mount_point = source_path_spec.parent

    searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)
    return file_system, searcher

  def PreprocessSource(
      self, source_path_specs, platform, resolver_context=None):
    """Preprocesses the source and fills the preprocessing object.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      platform: string that indicates the platform (operating system).
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.
    """
    for source_path_spec in source_path_specs:
      file_system, searcher = self.GetSourceFileSystemSearcher(
          source_path_spec, resolver_context=resolver_context)

      try:
        platform = preprocess_interface.GuessOS(searcher)
        if platform:
          self.knowledge_base.platform = platform

          preprocess_manager.PreprocessPluginsManager.RunPlugins(
              platform, searcher, self.knowledge_base)

      finally:
        file_system.Close()

      if platform:
        break

  def SetEnableDebugOutput(self, enable_debug_output):
    """Enables or disables debug output.

    Args:
      enable_debug_output: boolean value to indicate if the debug output
                           should be enabled.
    """
    self._enable_debug_output = enable_debug_output

  def SetEnableProfiling(
      self, enable_profiling, profiling_sample_rate=1000,
      profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if the profiling should
                        be enabled.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
      profiling_type: optional profiling type. The default is 'all'.
    """
    self._enable_profiling = enable_profiling
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

  def SetFilterObject(self, filter_object):
    """Sets the filter object.

    Args:
      filter_object: the filter object (instance of objectfilter.Filter).
    """
    self._filter_object = filter_object

  def SetMountPath(self, mount_path):
    """Sets the mount path.

    Args:
      mount_path: string containing the mount path.
    """
    self._mount_path = mount_path

  def SetProcessArchiveFiles(self, process_archive_files):
    """Sets the process archive files mode.

    Args:
      process_archive_files: boolean value to indicate if the worker should
                             scan for file entries inside files.
    """
    self._process_archive_files = process_archive_files

  # TODO: remove this functionality.
  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: string that contains the text to prepend to every
                    event object.
    """
    self._text_prepend = text_prepend

  def SignalAbort(self):
    """Signals the engine to abort."""
    logging.warning(u'Signalled abort.')
    self._event_queue_producer.SignalAbort()
    self._parse_error_queue_producer.SignalAbort()

  @classmethod
  def SupportsMemoryProfiling(cls):
    """Returns a boolean value to indicate if memory profiling is supported."""
    return profiler.GuppyMemoryProfiler.IsSupported()
