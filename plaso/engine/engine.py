# -*- coding: utf-8 -*-
"""The processing engine."""

import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import knowledge_base
from plaso.engine import processing_status
from plaso.engine import profiler
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager


class BaseEngine(object):
  """Class that defines the processing engine base.

  Attributes:
    knowledge_base: the knowledge base object (instance of KnowledgeBase).
  """

  # The interval of status updates in number of seconds.
  _STATUS_UPDATE_INTERVAL = 0.5

  def __init__(
      self, enable_profiling=False, profiling_directory=None,
      profiling_sample_rate=1000, profiling_type=u'all'):
    """Initializes an engine object.

    Args:
      enable_profiling (Optional[bool]): True if profiling should be enabled.
      profiling_directory (Optional[str]): path to the directory where
          the profiling sample files should be stored.
      profiling_sample_rate (Optional[int]): profiling sample rate.
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
    super(BaseEngine, self).__init__()
    self._abort = False
    self._enable_debug_output = False
    self._enable_profiling = enable_profiling
    self._processing_status = processing_status.ProcessingStatus()
    self._profiling_directory = profiling_directory
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

    self.knowledge_base = knowledge_base.KnowledgeBase()

  def GetSourceFileSystem(self, source_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec) of the file system.
      resolver_context: optional resolver context (instance of dfvfs.Context).
                        The default is None which will use the built in context
                        which is not multi process safe. Note that every thread
                        or process must have its own resolver context.

    Returns:
      A tuple of the file system (instance of dfvfs.FileSystem) and
      the mount point path specification (instance of path.PathSpec).
      The mount point path specification refers to either a directory or
      a volume on a storage media device or image. It is needed by the dfVFS
      file system searcher (instance of FileSystemSearcher) to indicate
      the base location of the file system.

    Raises:
      RuntimeError: if source file system path specification is not set.
    """
    if not source_path_spec:
      raise RuntimeError(u'Missing source path specification.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        source_path_spec, resolver_context=resolver_context)

    type_indicator = source_path_spec.type_indicator
    if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
      mount_point = source_path_spec
    else:
      mount_point = source_path_spec.parent

    return file_system, mount_point

  def PreprocessSources(self, source_path_specs, resolver_context=None):
    """Preprocesses the sources.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      resolver_context: optional resolver context (instance of dfvfs.Context).
                        The default is None which will use the built in context
                        which is not multi process safe. Note that every thread
                        or process must have its own resolver context.
    """
    for source_path_spec in source_path_specs:
      try:
        file_system, mount_point = self.GetSourceFileSystem(
            source_path_spec, resolver_context=resolver_context)
      except (RuntimeError, dfvfs_errors.BackEndError) as exception:
        logging.error(exception)
        continue

      try:
        searcher = file_system_searcher.FileSystemSearcher(
            file_system, mount_point)
        platform = preprocess_interface.GuessOS(searcher)
        if platform:
          self.knowledge_base.platform = platform

          preprocess_manager.PreprocessPluginsManager.RunPlugins(
              platform, file_system, mount_point, self.knowledge_base)

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

  def SignalAbort(self):
    """Signals the engine to abort."""
    logging.warning(u'Aborted by user.')
    self._abort = True

  @classmethod
  def SupportsMemoryProfiling(cls):
    """Returns a boolean value to indicate if memory profiling is supported."""
    return profiler.GuppyMemoryProfiler.IsSupported()
