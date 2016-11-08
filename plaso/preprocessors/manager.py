# -*- coding: utf-8 -*-
"""The preprocess plugins manager."""

import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.helpers import windows_path_resolver
from dfwinreg import interface as dfwinreg_interface
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry


class FileSystemWinRegistryFileReader(dfwinreg_interface.WinRegistryFileReader):
  """A file system-based Windows Registry file reader."""

  def __init__(self, file_system, mount_point, environment_variables=None):
    """Initializes a Windows Registry file reader object.

    Args:
      file_system (dfvfs.FileSytem): file system.
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
    """Create a Windows path resolver and sets the evironment variables.

    Args:
      file_system (dfvfs.FileSytem): file system.
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
      if name not in (u'systemroot', u'userprofile'):
        continue

      path_resolver.SetEnvironmentVariable(
          environment_variable.name, environment_variable.value)

    return path_resolver

  def _OpenPathSpec(self, path_specification, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path specification.

    Args:
      path_specification (dfvfs.PathSpec): path specfication.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    if not path_specification:
      return

    file_entry = self._file_system.GetFileEntryByPathSpec(path_specification)
    if file_entry is None:
      return

    file_object = file_entry.GetFileObject()
    if file_object is None:
      return

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage=ascii_codepage)

    try:
      registry_file.Open(file_object)
    except IOError as exception:
      logging.warning(
          u'Unable to open Windows Registry file with error: {0:s}'.format(
              exception))
      file_object.close()
      return

    return registry_file

  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    path_specification = self._path_resolver.ResolvePath(path)
    if path_specification is None:
      return

    return self._OpenPathSpec(path_specification)


class PreprocessPluginsManager(object):
  """Class that implements the preprocess plugins manager."""

  _file_system_plugin_classes = {}
  _registry_plugin_classes = {}

  @classmethod
  def _GetPluginObjects(cls, plugin_classes):
    """Returns all plugins.

    Args:
      plugin_classes (dict[str, type]): plugin classes with their class
          name as the key.

    Yields:
      PreprocessPlugin: preprocess plugin.
    """
    for plugin_class in iter(plugin_classes.values()):
      yield plugin_class()

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters a plugin class.

    Args:
      plugin_class (type): plugin class.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
    """
    if (plugin_class.__name__ not in cls._file_system_plugin_classes and
        plugin_class.__name__ not in cls._registry_plugin_classes):
      raise KeyError(
          u'Plugin class not set for name: {0:s}.'.format(
              plugin_class.__name__))

    if plugin_class.__name__ in cls._file_system_plugin_classes:
      del cls._file_system_plugin_classes[plugin_class.__name__]

    if plugin_class.__name__ in cls._registry_plugin_classes:
      del cls._registry_plugin_classes[plugin_class.__name__]

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers a plugin class.

    Args:
      plugin_class (type): plugin class.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    if (plugin_class.__name__ in cls._file_system_plugin_classes or
        plugin_class.__name__ in cls._registry_plugin_classes):
      raise KeyError(
          u'Plugin class already set for name: {0:s}.'.format(
              plugin_class.__name__))

    if hasattr(plugin_class, u'_REGISTRY_KEY_PATH'):
      cls._registry_plugin_classes[plugin_class.__name__] = plugin_class

    else:
      cls._file_system_plugin_classes[plugin_class.__name__] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers a plugin classes.

    Args:
      plugin_classes (list[type]): plugin classses.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)

  @classmethod
  def RunPlugins(cls, file_system, mount_point, knowledge_base):
    """Runs the preprocessing plugins.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
    """
    # TODO: bootstrap the artifact preprocessor.

    searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)

    for plugin_object in cls._GetPluginObjects(cls._file_system_plugin_classes):
      try:
        plugin_object.Run(searcher, knowledge_base)

      # All exceptions need to be caught here to prevent the manager
      # from being killed by an uncaught exception.
      except Exception as exception:  # pylint: disable=broad-except
        logging.warning(
            u'Preprocess plugin: {0:s} run failed with error: {1:s}'.format(
                plugin_object.plugin_name, exception))

    # Run the Registry plugins separately so we do not have to open
    # Registry files in every plugin.

    environment_variables = None
    if knowledge_base:
      environment_variables = knowledge_base.GetEnvironmentVariables()

    registry_file_reader = FileSystemWinRegistryFileReader(
        file_system, mount_point, environment_variables=environment_variables)
    win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)

    for plugin_object in cls._GetPluginObjects(cls._registry_plugin_classes):
      try:
        plugin_object.Run(win_registry, knowledge_base)

      # All exceptions need to be caught here to prevent the manager
      # from being killed by an uncaught exception.
      except Exception as exception:  # pylint: disable=broad-except
        logging.warning(
            u'Preprocess plugin: {0:s} run failed with error: {1:s}'.format(
                plugin_object.plugin_name, exception))

    if not knowledge_base.HasUserAccounts():
      logging.warning(u'Unable to find any user accounts on the system.')

