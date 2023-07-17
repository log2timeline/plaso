# -*- coding: utf-8 -*-
"""The processing engine."""

import os

from artifacts import errors as artifacts_errors
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import artifacts
from plaso.containers import sessions
from plaso.engine import artifact_filters
from plaso.engine import filter_file
from plaso.engine import knowledge_base
from plaso.engine import logger
from plaso.engine import path_filters
from plaso.engine import processing_status
from plaso.engine import profilers
from plaso.engine import yaml_filter_file
from plaso.lib import errors
from plaso.preprocessors import manager as preprocess_manager
from plaso.preprocessors import mediator as preprocess_mediator


class BaseEngine(object):
  """Processing engine interface.

  Attributes:
    knowledge_base (KnowledgeBase): knowledge base.
  """

  _WINDOWS_REGISTRY_FILES_ARTIFACT_NAMES = [
      'WindowsSystemRegistryFiles', 'WindowsUserRegistryFiles']

  def __init__(self):
    """Initializes an engine."""
    super(BaseEngine, self).__init__()
    self._abort = False
    self._analyzers_profiler = None
    self._artifacts_registry = None
    self._excluded_file_system_find_specs = None
    self._included_file_system_find_specs = None
    self._memory_profiler = None
    self._name = 'Main'
    self._processing_status = processing_status.ProcessingStatus()
    self._processing_profiler = None
    self._registry_find_specs = None
    self._serializers_profiler = None
    # The interval of status updates in number of seconds.
    self._status_update_interval = 0.5
    self._storage_profiler = None
    self._task_queue_profiler = None

    self.knowledge_base = knowledge_base.KnowledgeBase()

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

    if configuration.HaveProfileAnalyzers():
      identifier = '{0:s}-analyzers'.format(self._name)
      self._analyzers_profiler = profilers.AnalyzersProfiler(
          identifier, configuration)
      self._analyzers_profiler.Start()

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

    if self._analyzers_profiler:
      self._analyzers_profiler.Stop()
      self._analyzers_profiler = None

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

  def BuildArtifactsRegistry(
      self, artifact_definitions_path, custom_artifacts_path):
    """Builds an artificats definition registry.

    Args:
      artifact_definitions_path (str): path to artifact definitions directory
          or file.
      custom_artifacts_path (str): path to custom artifact definitions
          directory or file.

    Raises:
      BadConfigOption: if artifact definitions cannot be read.
    """
    if not artifact_definitions_path:
      raise errors.BadConfigOption('Missing artifact definitions path.')

    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    try:
      if os.path.isdir(artifact_definitions_path):
        registry.ReadFromDirectory(reader, artifact_definitions_path)
      else:
        registry.ReadFromFile(reader, artifact_definitions_path)

    except (KeyError, artifacts_errors.FormatError) as exception:
      raise errors.BadConfigOption((
          'Unable to read artifact definitions from: {0:s} with error: '
          '{1!s}').format(artifact_definitions_path, exception))

    if custom_artifacts_path:
      try:
        if os.path.isdir(custom_artifacts_path):
          registry.ReadFromDirectory(reader, custom_artifacts_path)
        else:
          registry.ReadFromFile(reader, custom_artifacts_path)

      except (KeyError, artifacts_errors.FormatError) as exception:
        raise errors.BadConfigOption((
            'Unable to read custom artifact definitions from: {0:s} with '
            'error: {1!s}').format(custom_artifacts_path, exception))

    self._artifacts_registry = registry

  def BuildCollectionFilters(
      self, environment_variables, user_accounts, artifact_filter_names=None,
      filter_file_path=None):
    """Builds collection filters from artifacts or filter file if available.

    Args:
      environment_variables (list[EnvironmentVariableArtifact]):
          environment variables.
      user_accounts (list[UserAccountArtifact]): user accounts.
      artifact_filter_names (Optional[list[str]]): names of artifact
          definitions that are used for filtering file system and Windows
          Registry key paths.
      filter_file_path (Optional[str]): path of filter file.

    Raises:
      InvalidFilter: if no valid file system find specifications are built.
    """
    filters_helper = None

    if artifact_filter_names:
      logger.debug(
          'building find specification based on artifacts: {0:s}'.format(
              ', '.join(artifact_filter_names)))

      filters_helper = artifact_filters.ArtifactDefinitionsFiltersHelper(
          self._artifacts_registry)
      filters_helper.BuildFindSpecs(
          artifact_filter_names, environment_variables=environment_variables,
          user_accounts=user_accounts)

      # If the user selected Windows Registry artifacts we have to ensure
      # the Windows Registry files are parsed.
      if filters_helper.registry_find_specs:
        filters_helper.BuildFindSpecs(
            self._WINDOWS_REGISTRY_FILES_ARTIFACT_NAMES,
            environment_variables=environment_variables,
            user_accounts=user_accounts)

      if not filters_helper.file_system_find_specs:
        raise errors.InvalidFilter(
            'No valid file system find specifications were built from '
            'artifacts.')

      self._included_file_system_find_specs = (
          filters_helper.file_system_find_specs)
      self._registry_find_specs = filters_helper.registry_find_specs

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

      filters_helper = path_filters.PathCollectionFiltersHelper()
      filters_helper.BuildFindSpecs(
          filter_file_path_filters, environment_variables=environment_variables)

      if (not filters_helper.excluded_file_system_find_specs and
          not filters_helper.included_file_system_find_specs):
        raise errors.InvalidFilter((
            'No valid file system find specifications were built from filter '
            'file: {0:s}.').format(filter_file_path))

      self._excluded_file_system_find_specs = (
          filters_helper.excluded_file_system_find_specs)
      self._included_file_system_find_specs = (
          filters_helper.included_file_system_find_specs)

  # pylint: disable=too-many-arguments
  @classmethod
  def CreateSession(
      cls, artifact_filter_names=None, command_line_arguments=None,
      debug_mode=False, filter_file_path=None, preferred_encoding='utf-8'):
    """Creates a session attribute container.

    Args:
      artifact_filter_names (Optional[list[str]]): names of artifact definitions
          that are used for filtering file system and Windows Registry
          key paths.
      command_line_arguments (Optional[str]): the command line arguments.
      debug_mode (Option[bool]): True if debug mode was enabled.
      filter_file_path (Optional[str]): path to a file with find specifications.
      preferred_encoding (Optional[str]): preferred encoding.

    Returns:
      Session: session attribute container.
    """
    session = sessions.Session()

    session.artifact_filters = artifact_filter_names
    session.command_line_arguments = command_line_arguments
    session.debug_mode = debug_mode
    session.filter_file = filter_file_path
    session.preferred_encoding = preferred_encoding

    return session

  def GetCollectionExcludedFindSpecs(self):
    """Retrieves find specifications to exclude from collection.

    Returns:
      list[dfvfs.FindSpec]: find specifications to exclude from collection.
    """
    return self._excluded_file_system_find_specs or []

  def GetCollectionIncludedFindSpecs(self):
    """Retrieves find specifications to include in collection.

    Returns:
      list[dfvfs.FindSpec]: find specifications to include in collection.
    """
    return self._included_file_system_find_specs or []

  def GetSourceFileSystem(self, file_system_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    Args:
      file_system_path_spec (dfvfs.PathSpec): path specifications of
          the source file system to process.
      resolver_context (dfvfs.Context): resolver context.

    Returns:
      tuple: containing:

        dfvfs.FileSystem: file system
        path.PathSpec: mount point path specification. The mount point path
            specification refers to either a directory or a volume on a storage
            media device or image. It is needed by the dfVFS file system
            to indicate the base location of the file system.

    Raises:
      RuntimeError: if source file system path specification is not set.
    """
    if not file_system_path_spec:
      raise RuntimeError('Missing source file system path specification.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        file_system_path_spec, resolver_context=resolver_context)

    type_indicator = file_system_path_spec.type_indicator
    if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
      mount_point = file_system_path_spec
    else:
      mount_point = file_system_path_spec.parent

    return file_system, mount_point

  def PreprocessSource(
      self, file_system_path_specs, storage_writer, resolver_context=None):
    """Preprocesses a source.

    Args:
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.
      storage_writer (StorageWriter): storage writer.
      resolver_context (Optional[dfvfs.Context]): resolver context.

    Returns:
      list[SystemConfigurationArtifact]: system configurations found in
          the source.
    """
    mediator = preprocess_mediator.PreprocessMediator(storage_writer)

    detected_operating_systems = []
    system_configurations = []
    for path_spec in file_system_path_specs:
      try:
        file_system, mount_point = self.GetSourceFileSystem(
            path_spec, resolver_context=resolver_context)
      except (RuntimeError, dfvfs_errors.BackEndError) as exception:
        logger.error(exception)
        continue

      preprocess_manager.PreprocessPluginsManager.RunPlugins(
          self._artifacts_registry, file_system, mount_point, mediator)

      operating_system = mediator.GetValue('operating_system')
      if not operating_system:
        continue

      detected_operating_systems.append(operating_system)

      system_configuration = artifacts.SystemConfigurationArtifact(
          code_page=mediator.code_page, language=mediator.language)
      # Ensure environment_variables is a list otherwise serialization will
      # fail.
      system_configuration.environment_variables = list(
          mediator.GetEnvironmentVariables())
      system_configuration.hostname = mediator.hostname
      system_configuration.keyboard_layout = mediator.GetValue(
          'keyboard_layout')
      system_configuration.operating_system = mediator.GetValue(
          'operating_system')
      system_configuration.operating_system_product = mediator.GetValue(
          'operating_system_product')
      system_configuration.operating_system_version = mediator.GetValue(
          'operating_system_version')
      # TODO: add support for multi file system system configurations.
      system_configuration.path_specs = [path_spec]

      if mediator.time_zone:
        system_configuration.time_zone = mediator.time_zone.zone

      system_configurations.append(system_configuration)

      mediator.Reset()

    if system_configurations:
      # TODO: kept for backwards compatibility.
      self.knowledge_base.ReadSystemConfigurationArtifact(
          system_configurations[0])
      for environment_variable in system_configuration.environment_variables:
        self.knowledge_base.AddEnvironmentVariable(environment_variable)

    return system_configurations

  def SetStatusUpdateInterval(self, status_update_interval):
    """Sets the status update interval.

    Args:
      status_update_interval (float): status update interval.
    """
    self._status_update_interval = status_update_interval
