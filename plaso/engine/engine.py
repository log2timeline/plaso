# -*- coding: utf-8 -*-
"""The processing engine."""

from __future__ import unicode_literals

import os

from artifacts import errors as artifacts_errors
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.engine import artifact_filters
from plaso.engine import filter_file
from plaso.engine import knowledge_base
from plaso.engine import logger
from plaso.engine import path_filters
from plaso.engine import processing_status
from plaso.engine import profilers
from plaso.engine import yaml_filter_file
from plaso.lib import definitions
from plaso.lib import errors
from plaso.preprocessors import manager as preprocess_manager


class BaseEngine(object):
  """Processing engine interface.

  Attributes:
    collection_filters_helper (CollectionFiltersHelper): collection filters
        helper.
    knowledge_base (KnowledgeBase): knowledge base.
  """

  # The interval of status updates in number of seconds.
  _STATUS_UPDATE_INTERVAL = 0.5

  _WINDOWS_REGISTRY_FILES_ARTIFACT_NAMES = [
      'WindowsSystemRegistryFiles', 'WindowsUserRegistryFiles']

  def __init__(self):
    """Initializes an engine."""
    super(BaseEngine, self).__init__()
    self._abort = False
    self._memory_profiler = None
    self._name = 'Main'
    self._processing_status = processing_status.ProcessingStatus()
    self._processing_profiler = None
    self._serializers_profiler = None
    self._storage_profiler = None
    self._task_queue_profiler = None

    self.collection_filters_helper = None
    self.knowledge_base = knowledge_base.KnowledgeBase()

  def _DetermineOperatingSystem(self, searcher):
    """Tries to determine the underlying operating system.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.

    Returns:
      str: operating system for example "Windows". This should be one of
          the values in definitions.OPERATING_SYSTEM_FAMILIES.
    """
    find_specs = [
        file_system_searcher.FindSpec(
            case_sensitive=False, location='/etc',
            location_separator='/'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='/System/Library',
            location_separator='/'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\Windows\\System32',
            location_separator='\\'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\WINNT\\System32',
            location_separator='\\'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\WINNT35\\System32',
            location_separator='\\'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\WTSRV\\System32',
            location_separator='\\')]

    locations = []
    for path_spec in searcher.Find(find_specs=find_specs):
      relative_path = searcher.GetRelativePath(path_spec)
      if relative_path:
        locations.append(relative_path.lower())

    # We need to check for both forward and backward slashes since the path
    # spec will be OS dependent, as in running the tool on Windows will return
    # Windows paths (backward slash) vs. forward slash on *NIX systems.
    windows_locations = set([
        '/windows/system32', '\\windows\\system32', '/winnt/system32',
        '\\winnt\\system32', '/winnt35/system32', '\\winnt35\\system32',
        '\\wtsrv\\system32', '/wtsrv/system32'])

    operating_system = definitions.OPERATING_SYSTEM_FAMILY_UNKNOWN
    if windows_locations.intersection(set(locations)):
      operating_system = definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT

    elif '/system/library' in locations:
      operating_system = definitions.OPERATING_SYSTEM_FAMILY_MACOS

    elif '/etc' in locations:
      operating_system = definitions.OPERATING_SYSTEM_FAMILY_LINUX

    return operating_system

  def _StartProfiling(self, configuration):
    """Starts profiling.

    Args:
      configuration (ProfilingConfiguration): profiling configuration.
    """
    if not configuration:
      return

    if configuration.HaveProfileMemory():
      self._memory_profiler = profilers.MemoryProfiler(
          self._name, configuration)
      self._memory_profiler.Start()

    if configuration.HaveProfileProcessing():
      identifier = '{0:s}-processing'.format(self._name)
      self._processing_profiler = profilers.ProcessingProfiler(
          identifier, configuration)
      self._processing_profiler.Start()

    if configuration.HaveProfileSerializers():
      identifier = '{0:s}-serializers'.format(self._name)
      self._serializers_profiler = profilers.SerializersProfiler(
          identifier, configuration)
      self._serializers_profiler.Start()

    if configuration.HaveProfileStorage():
      self._storage_profiler = profilers.StorageProfiler(
          self._name, configuration)
      self._storage_profiler.Start()

    if configuration.HaveProfileTaskQueue():
      self._task_queue_profiler = profilers.TaskQueueProfiler(
          self._name, configuration)
      self._task_queue_profiler.Start()

  def _StopProfiling(self):
    """Stops profiling."""
    if self._memory_profiler:
      self._memory_profiler.Stop()
      self._memory_profiler = None

    if self._processing_profiler:
      self._processing_profiler.Stop()
      self._processing_profiler = None

    if self._serializers_profiler:
      self._serializers_profiler.Stop()
      self._serializers_profiler = None

    if self._storage_profiler:
      self._storage_profiler.Stop()
      self._storage_profiler = None

    if self._task_queue_profiler:
      self._task_queue_profiler.Stop()
      self._task_queue_profiler = None

  @classmethod
  def CreateSession(
      cls, artifact_filter_names=None, command_line_arguments=None,
      debug_mode=False, filter_file_path=None, preferred_encoding='utf-8',
      preferred_time_zone=None, preferred_year=None):
    """Creates a session attribute container.

    Args:
      artifact_filter_names (Optional[list[str]]): names of artifact definitions
          that are used for filtering file system and Windows Registry
          key paths.
      command_line_arguments (Optional[str]): the command line arguments.
      debug_mode (bool): True if debug mode was enabled.
      filter_file_path (Optional[str]): path to a file with find specifications.
      preferred_encoding (Optional[str]): preferred encoding.
      preferred_time_zone (Optional[str]): preferred time zone.
      preferred_year (Optional[int]): preferred year.

    Returns:
      Session: session attribute container.
    """
    session = sessions.Session()

    session.artifact_filters = artifact_filter_names
    session.command_line_arguments = command_line_arguments
    session.debug_mode = debug_mode
    session.filter_file = filter_file_path
    session.preferred_encoding = preferred_encoding
    session.preferred_time_zone = preferred_time_zone
    session.preferred_year = preferred_year

    return session

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
      raise RuntimeError('Missing source path specification.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        source_path_spec, resolver_context=resolver_context)

    type_indicator = source_path_spec.type_indicator
    if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
      mount_point = source_path_spec
    else:
      mount_point = source_path_spec.parent

    return file_system, mount_point

  def PreprocessSources(
      self, artifacts_registry_object, source_path_specs,
      resolver_context=None):
    """Preprocesses the sources.

    Args:
      artifacts_registry_object (artifacts.ArtifactDefinitionsRegistry):
          artifact definitions registry.
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      resolver_context (Optional[dfvfs.Context]): resolver context.
    """
    detected_operating_systems = []
    for source_path_spec in source_path_specs:
      try:
        file_system, mount_point = self.GetSourceFileSystem(
            source_path_spec, resolver_context=resolver_context)
      except (RuntimeError, dfvfs_errors.BackEndError) as exception:
        logger.error(exception)
        continue

      try:
        searcher = file_system_searcher.FileSystemSearcher(
            file_system, mount_point)

        operating_system = self._DetermineOperatingSystem(searcher)
        if operating_system != definitions.OPERATING_SYSTEM_FAMILY_UNKNOWN:
          preprocess_manager.PreprocessPluginsManager.RunPlugins(
              artifacts_registry_object, file_system, mount_point,
              self.knowledge_base)

          detected_operating_systems.append(operating_system)

      finally:
        file_system.Close()

    if detected_operating_systems:
      logger.info('Preprocessing detected operating systems: {0:s}'.format(
          ', '.join(detected_operating_systems)))
      self.knowledge_base.SetValue(
          'operating_system', detected_operating_systems[0])

  def BuildCollectionFilters(
      self, artifact_definitions_path, custom_artifacts_path,
      knowledge_base_object, artifact_filter_names=None, filter_file_path=None):
    """Builds collection filters from artifacts or filter file if available.

    Args:
      artifact_definitions_path (str): path to artifact definitions file.
      custom_artifacts_path (str): path to custom artifact definitions file.
      knowledge_base_object (KnowledgeBase): knowledge base.
      artifact_filter_names (Optional[list[str]]): names of artifact
          definitions that are used for filtering file system and Windows
          Registry key paths.
      filter_file_path (Optional[str]): path of filter file.

    Raises:
      InvalidFilter: if no valid file system find specifications are built.
    """
    environment_variables = knowledge_base_object.GetEnvironmentVariables()
    if artifact_filter_names:
      logger.debug(
          'building find specification based on artifacts: {0:s}'.format(
              ', '.join(artifact_filter_names)))

      artifacts_registry_object = BaseEngine.BuildArtifactsRegistry(
          artifact_definitions_path, custom_artifacts_path)
      self.collection_filters_helper = (
          artifact_filters.ArtifactDefinitionsFiltersHelper(
              artifacts_registry_object, knowledge_base_object))
      self.collection_filters_helper.BuildFindSpecs(
          artifact_filter_names, environment_variables=environment_variables)

      # If the user selected Windows Registry artifacts we have to ensure
      # the Windows Registry files are parsed.
      if self.collection_filters_helper.registry_find_specs:
        self.collection_filters_helper.BuildFindSpecs(
            self._WINDOWS_REGISTRY_FILES_ARTIFACT_NAMES,
            environment_variables=environment_variables)

      if not self.collection_filters_helper.included_file_system_find_specs:
        raise errors.InvalidFilter(
            'No valid file system find specifications were built from '
            'artifacts.')

    elif filter_file_path:
      logger.debug(
          'building find specification based on filter file: {0:s}'.format(
              filter_file_path))

      filter_file_path_lower = filter_file_path.lower()
      if (filter_file_path_lower.endswith('.yaml') or
          filter_file_path_lower.endswith('.yml')):
        filter_file_object = yaml_filter_file.YAMLFilterFile()
      else:
        filter_file_object = filter_file.FilterFile()

      filter_file_path_filters = filter_file_object.ReadFromFile(
          filter_file_path)

      self.collection_filters_helper = (
          path_filters.PathCollectionFiltersHelper())
      self.collection_filters_helper.BuildFindSpecs(
          filter_file_path_filters, environment_variables=environment_variables)

      if (not self.collection_filters_helper.excluded_file_system_find_specs and
          not self.collection_filters_helper.included_file_system_find_specs):
        raise errors.InvalidFilter((
            'No valid file system find specifications were built from filter '
            'file: {0:s}.').format(filter_file_path))

  @classmethod
  def BuildArtifactsRegistry(
      cls, artifact_definitions_path, custom_artifacts_path):
    """Build Find Specs from artifacts or filter file if available.

    Args:
       artifact_definitions_path (str): path to artifact definitions file.
       custom_artifacts_path (str): path to custom artifact definitions file.

    Returns:
      artifacts.ArtifactDefinitionsRegistry: artifact definitions registry.

    Raises:
      BadConfigOption: if artifact definitions cannot be read.
    """
    if artifact_definitions_path and not os.path.isdir(
        artifact_definitions_path):
      raise errors.BadConfigOption(
          'No such artifacts filter file: {0:s}.'.format(
              artifact_definitions_path))

    if custom_artifacts_path and not os.path.isfile(custom_artifacts_path):
      raise errors.BadConfigOption(
          'No such artifacts filter file: {0:s}.'.format(custom_artifacts_path))

    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    try:
      registry.ReadFromDirectory(reader, artifact_definitions_path)

    except (KeyError, artifacts_errors.FormatError) as exception:
      raise errors.BadConfigOption((
          'Unable to read artifact definitions from: {0:s} with error: '
          '{1!s}').format(artifact_definitions_path, exception))

    if custom_artifacts_path:
      try:
        registry.ReadFromFile(reader, custom_artifacts_path)

      except (KeyError, artifacts_errors.FormatError) as exception:
        raise errors.BadConfigOption((
            'Unable to read artifact definitions from: {0:s} with error: '
            '{1!s}').format(custom_artifacts_path, exception))

    return registry
