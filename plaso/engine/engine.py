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
from plaso.lib import definitions
from plaso.preprocessors import manager as preprocess_manager


class BaseEngine(object):
  """Class that defines the processing engine base.

  Attributes:
    knowledge_base: the knowledge base object (instance of KnowledgeBase).
  """

  # The interval of status updates in number of seconds.
  _STATUS_UPDATE_INTERVAL = 0.5

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
    self._debug_output = debug_output
    self._enable_profiling = enable_profiling
    self._processing_status = processing_status.ProcessingStatus()
    self._profiling_directory = profiling_directory
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

    self.knowledge_base = knowledge_base.KnowledgeBase()

  def _GuessOS(self, searcher):
    """Returns a string representing what we think the underlying OS is.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.

    Returns:
      str: operating system for example "Windows". This should be one of
          the values in definitions.OPERATING_SYSTEMS.
    """
    find_specs = [
        file_system_searcher.FindSpec(
            location=u'/etc', case_sensitive=False),
        file_system_searcher.FindSpec(
            location=u'/System/Library', case_sensitive=False),
        file_system_searcher.FindSpec(
            location=u'/Windows/System32', case_sensitive=False),
        file_system_searcher.FindSpec(
            location=u'/WINNT/System32', case_sensitive=False),
        file_system_searcher.FindSpec(
            location=u'/WINNT35/System32', case_sensitive=False),
        file_system_searcher.FindSpec(
            location=u'/WTSRV/System32', case_sensitive=False)]

    locations = []
    for path_spec in searcher.Find(find_specs=find_specs):
      relative_path = searcher.GetRelativePath(path_spec)
      if relative_path:
        locations.append(relative_path.lower())

    # We need to check for both forward and backward slashes since the path
    # spec will be OS dependent, as in running the tool on Windows will return
    # Windows paths (backward slash) vs. forward slash on *NIX systems.
    windows_locations = set([
        u'/windows/system32', u'\\windows\\system32', u'/winnt/system32',
        u'\\winnt\\system32', u'/winnt35/system32', u'\\winnt35\\system32',
        u'\\wtsrv\\system32', u'/wtsrv/system32'])

    if windows_locations.intersection(set(locations)):
      return definitions.OPERATING_SYSTEM_WINDOWS

    if u'/system/library' in locations:
      return definitions.OPERATING_SYSTEM_MACOSX

    if u'/etc' in locations:
      return definitions.OPERATING_SYSTEM_LINUX

    return definitions.OPERATING_SYSTEM_UNKNOWN

  def GetSourceFileSystem(self, source_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    Args:
      source_path_spec (dfvfs.PathSpec): path specifications of the sources
          to process.
      resolver_context (dfvfs.Context): resolver context.

    Returns:
      tuple: containing:

        dfvfs.FileSystem: file system
        path.PathSpec: mount point path specification. The mount point path
            specification refers to either a directory or a volume on a storage
            media device or image. It is needed by the dfVFS file system
            searcher (FileSystemSearcher) to indicate the base location of
            the file system.

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
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      resolver_context (dfvfs.Context): resolver context.
    """
    platform = None
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

        platform = self._GuessOS(searcher)
        logging.info(u'Preprocessing detected platform: {0:s}'.format(platform))
        if platform:
          self.knowledge_base.platform = platform

        preprocess_manager.PreprocessPluginsManager.RunPlugins(
            file_system, mount_point, self.knowledge_base)

      finally:
        file_system.Close()

      if platform:
        self.knowledge_base.platform = platform
        break

  @classmethod
  def SupportsMemoryProfiling(cls):
    """Determines if memory profiling is supported.

    Returns:
      bool: True if memory profiling is supported.
    """
    return profiler.GuppyMemoryProfiler.IsSupported()
