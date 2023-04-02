# -*- coding: utf-8 -*-
"""The preprocess plugins manager."""

from dfvfs.helpers import file_system_searcher
from dfvfs.helpers import windows_path_resolver
from dfvfs.lib import errors as dfvfs_errors
from dfwinreg import interface as dfwinreg_interface
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher

from plaso.lib import errors
from plaso.preprocessors import interface
from plaso.preprocessors import logger


class FileSystemWinRegistryFileReader(dfwinreg_interface.WinRegistryFileReader):
  """A file system-based Windows Registry file reader."""

  def __init__(self, file_system, mount_point, environment_variables=None):
    """Initializes a Windows Registry file reader object.

    Args:
      file_system (dfvfs.FileSystem): file system.
      mount_point (dfvfs.PathSpec): mount point path specification.
      environment_variables (Optional[list[EnvironmentVariableArtifact]]):
          environment variables.
    """
    super(FileSystemWinRegistryFileReader, self).__init__()
    self._file_system = file_system
    self._path_resolver = self._CreateWindowsPathResolver(
        file_system, mount_point, environment_variables=environment_variables)

  def _CreateWindowsPathResolver(
      self, file_system, mount_point, environment_variables):
    """Create a Windows path resolver and sets the environment variables.

    Args:
      file_system (dfvfs.FileSystem): file system.
      mount_point (dfvfs.PathSpec): mount point path specification.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.

    Returns:
      dfvfs.WindowsPathResolver: Windows path resolver.
    """
    if environment_variables is None:
      environment_variables = []

    path_resolver = windows_path_resolver.WindowsPathResolver(
        file_system, mount_point)

    for environment_variable in environment_variables:
      name = environment_variable.name.lower()
      if name not in ('systemroot', 'userprofile'):
        continue

      path_resolver.SetEnvironmentVariable(
          environment_variable.name, environment_variable.value)

    return path_resolver

  def _OpenPathSpec(self, path_specification, ascii_codepage='cp1252'):
    """Opens the Windows Registry file specified by the path specification.

    Args:
      path_specification (dfvfs.PathSpec): path specification.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    if not path_specification:
      return None

    file_entry = self._file_system.GetFileEntryByPathSpec(path_specification)
    if file_entry is None:
      return None

    file_object = file_entry.GetFileObject()
    if file_object is None:
      return None

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage=ascii_codepage)

    try:
      registry_file.Open(file_object)
    except IOError as exception:
      logger.warning(
          'Unable to open Windows Registry file with error: {0!s}'.format(
              exception))
      return None

    return registry_file

  def Open(self, path, ascii_codepage='cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    path_specification = None

    try:
      path_specification = self._path_resolver.ResolvePath(path)
    except dfvfs_errors.BackEndError as exception:
      logger.warning((
          'Unable to open Windows Registry file: {0:s} with error: '
          '{1!s}').format(path, exception))

    if path_specification is None:
      return None

    return self._OpenPathSpec(path_specification)


class PreprocessPluginsManager(object):
  """Preprocess plugins manager."""

  _plugins = {}
  _file_system_plugins = {}
  # TODO: rename knowledge base plugins.
  _knowledge_base_plugins = {}
  _windows_registry_plugins = {}

  @classmethod
  def CollectFromFileSystem(
      cls, artifacts_registry, mediator, searcher, file_system):
    """Collects values from Windows Registry values.

    Args:
      artifacts_registry (artifacts.ArtifactDefinitionsRegistry): artifacts
          definitions registry.
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.
    """
    for preprocess_plugin in cls._file_system_plugins.values():
      artifact_definition = None
      if preprocess_plugin.ARTIFACT_DEFINITION_NAME:
        artifact_definition = artifacts_registry.GetDefinitionByName(
            preprocess_plugin.ARTIFACT_DEFINITION_NAME)
        if not artifact_definition:
          artifact_definition = artifacts_registry.GetDefinitionByAlias(
              preprocess_plugin.ARTIFACT_DEFINITION_NAME)
        if not artifact_definition:
          logger.warning('Missing artifact definition: {0:s}'.format(
              preprocess_plugin.ARTIFACT_DEFINITION_NAME))
          continue

      logger.debug((
          'Running file system preprocessor plugin: {0:s} with artifact '
          'definition: {1:s}').format(
              preprocess_plugin.__class__.__name__,
              preprocess_plugin.ARTIFACT_DEFINITION_NAME or 'N/A'))

      try:
        preprocess_plugin.Collect(
            mediator, artifact_definition, searcher, file_system)
      except (IOError, errors.PreProcessFail) as exception:
        logger.warning((
            'Preprocessor plugin: {0:s} with artifact definition: {1:s} '
            'was unable to collect value with error: {2!s}').format(
                preprocess_plugin.__class__.__name__,
                preprocess_plugin.ARTIFACT_DEFINITION_NAME or 'N/A',
                exception))

  @classmethod
  def CollectFromKnowledgeBase(cls, mediator):
    """Collects values from knowledge base values.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
    """
    for preprocess_plugin in cls._knowledge_base_plugins.values():
      logger.debug('Running knowledge base preprocessor plugin: {0:s}'.format(
          preprocess_plugin.__class__.__name__))
      try:
        preprocess_plugin.Collect(mediator)
      except errors.PreProcessFail as exception:
        logger.warning(
            'Unable to collect knowledge base value with error: {0!s}'.format(
                exception))

  @classmethod
  def CollectFromWindowsRegistry(cls, artifacts_registry, mediator, searcher):
    """Collects values from Windows Registry values.

    Args:
      artifacts_registry (artifacts.ArtifactDefinitionsRegistry): artifacts
          definitions registry.
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      searcher (dfwinreg.WinRegistrySearcher): Windows Registry searcher to
          preprocess the Windows Registry.
    """
    # TODO: define preprocessing plugin dependency and sort preprocess_plugins
    # for now sort alphabetically to ensure WindowsAvailableTimeZones is run
    # before WindowsTimezone.
    for _, preprocess_plugin in sorted(cls._windows_registry_plugins.items()):
      artifact_definition = artifacts_registry.GetDefinitionByName(
          preprocess_plugin.ARTIFACT_DEFINITION_NAME)
      if not artifact_definition:
        artifact_definition = artifacts_registry.GetDefinitionByAlias(
            preprocess_plugin.ARTIFACT_DEFINITION_NAME)
      if not artifact_definition:
        logger.warning('Missing artifact definition: {0:s}'.format(
            preprocess_plugin.ARTIFACT_DEFINITION_NAME))
        continue

      logger.debug('Running Windows Registry preprocessor plugin: {0:s}'.format(
          preprocess_plugin.ARTIFACT_DEFINITION_NAME))
      try:
        preprocess_plugin.Collect(mediator, artifact_definition, searcher)
      except (IOError, errors.PreProcessFail) as exception:
        logger.warning((
            'Unable to collect value from artifact definition: {0:s} '
            'with error: {1!s}').format(
                preprocess_plugin.ARTIFACT_DEFINITION_NAME, exception))

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters an preprocess plugin class.

    Args:
      plugin_class (type): preprocess plugin class.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
      TypeError: if the source type of the plugin class is not supported.
    """
    name = (getattr(plugin_class, 'ARTIFACT_DEFINITION_NAME', None) or
            plugin_class.__name__)
    name = name.lower()
    if name not in cls._plugins:
      raise KeyError(
          'Artifact plugin class not set for name: {0:s}.'.format(name))

    del cls._plugins[name]

    if name in cls._file_system_plugins:
      del cls._file_system_plugins[name]

    if name in cls._knowledge_base_plugins:
      del cls._knowledge_base_plugins[name]

    if name in cls._windows_registry_plugins:
      del cls._windows_registry_plugins[name]

  @classmethod
  def GetNames(cls):
    """Retrieves the names of the registered artifact definitions.

    Returns:
      list[str]: registered artifact definitions names.
    """
    names = []
    for plugin_class in cls._plugins.values():
      name = getattr(plugin_class, 'ARTIFACT_DEFINITION_NAME', None)
      if name:
        names.append(name)

    return names

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers an preprocess plugin class.

    Args:
      plugin_class (type): preprocess plugin class.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
      TypeError: if the source type of the plugin class is not supported.
    """
    name = (getattr(plugin_class, 'ARTIFACT_DEFINITION_NAME', None) or
            plugin_class.__name__)
    name = name.lower()
    if name in cls._plugins:
      raise KeyError(
          'Artifact plugin class already set for name: {0:s}.'.format(name))

    preprocess_plugin = plugin_class()

    cls._plugins[name] = preprocess_plugin

    if isinstance(
        preprocess_plugin, interface.FileSystemArtifactPreprocessorPlugin):
      cls._file_system_plugins[name] = preprocess_plugin

    elif isinstance(
        preprocess_plugin, interface.KnowledgeBasePreprocessorPlugin):
      cls._knowledge_base_plugins[name] = preprocess_plugin

    elif isinstance(
        preprocess_plugin,
        interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
      cls._windows_registry_plugins[name] = preprocess_plugin

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers preprocess plugin classes.

    Args:
      plugin_classes (list[type]): preprocess plugin classes.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)

  @classmethod
  def RunPlugins(cls, artifacts_registry, file_system, mount_point, mediator):
    """Runs the preprocessing plugins.

    Args:
      artifacts_registry (artifacts.ArtifactDefinitionsRegistry): artifacts
          definitions registry.
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
    """
    searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)

    cls.CollectFromFileSystem(
        artifacts_registry, mediator, searcher, file_system)

    # Run the Registry plugins separately so we do not have to open
    # Registry files for every preprocess plugin.

    environment_variables = mediator.GetEnvironmentVariables()

    registry_file_reader = FileSystemWinRegistryFileReader(
        file_system, mount_point, environment_variables=environment_variables)
    win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    cls.CollectFromWindowsRegistry(artifacts_registry, mediator, searcher)

    cls.CollectFromKnowledgeBase(mediator)
