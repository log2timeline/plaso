# -*- coding: utf-8 -*-
"""The processing engine."""

from dfvfs.helpers import file_system_searcher
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import knowledge_base
from plaso.engine import processing_status
from plaso.engine import profiler
from plaso.engine import queue
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager


class BaseEngine(object):
  """Class that defines the processing engine base.

  Attributes:
    event_object_queue: the event object queue (instance of Queue).
    knowledge_base: the knowledge base object (instance of KnowledgeBase).
  """

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
    self._path_spec_queue = path_spec_queue
    self._parse_error_queue = parse_error_queue
    self._parse_error_queue_producer = queue.ItemQueueProducer(
        parse_error_queue)
    self._processing_status = processing_status.ProcessingStatus()
    self._profiling_sample_rate = 1000
    self._profiling_type = u'all'

    self.event_object_queue = event_object_queue
    self.knowledge_base = knowledge_base.KnowledgeBase()

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

  def SignalAbort(self):
    """Signals the engine to abort."""
    self._event_queue_producer.SignalAbort()
    self._parse_error_queue_producer.SignalAbort()

  @classmethod
  def SupportsMemoryProfiling(cls):
    """Returns a boolean value to indicate if memory profiling is supported."""
    return profiler.GuppyMemoryProfiler.IsSupported()
