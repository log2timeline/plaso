# -*- coding: utf-8 -*-
"""The preprocess plugins manager."""

import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.helpers import windows_path_resolver

from plaso.dfwinreg import interface as dfwinreg_interface
from plaso.dfwinreg import regf as dfwinreg_regf
from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.lib import errors


class FileSystemWinRegistryFileReader(dfwinreg_interface.WinRegistryFileReader):
  """A file system-based Windows Registry file reader."""

  def __init__(self, file_system, mount_point, path_attributes=None):
    """Initializes a Windows Registry file reader object.

    Args:
      file_system: the file system object (instance of vfs.FileSystem).
      mount_point: the mount point path specification (instance of
                   path.PathSpec).
      path_attributes: optional dictionary of path attributes.
    """
    super(FileSystemWinRegistryFileReader, self).__init__()
    self._file_system = file_system
    self._path_resolver = windows_path_resolver.WindowsPathResolver(
        file_system, mount_point)

    if path_attributes:
      for attribute_name, attribute_value in iter(path_attributes.items()):
        # TODO: fix the call to this class and make sure only relevant
        # values are passed.
        if attribute_name == u'systemroot':
          self._path_resolver.SetEnvironmentVariable(
              u'SystemRoot', attribute_value)

  def _OpenPathSpec(self, path_spec, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path specification.

    Args:
      path_spec: a path specfication (instance of dfvfs.PathSpec).
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    if not path_spec:
      return

    file_entry = self._file_system.GetFileEntryByPathSpec(path_spec)
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
      path: the path of the Windows Registry file.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    path_spec = self._path_resolver.ResolvePath(path)
    if path_spec is None:
      return

    return self._OpenPathSpec(path_spec)


class PreprocessPluginsManager(object):
  """Class that implements the preprocess plugins manager."""

  _plugin_classes = {}
  _registry_plugin_classes = {}

  @classmethod
  def _GetPluginsByWeight(cls, plugin_classes, platform, weight):
    """Returns all plugins for a specific platform of a certain weight.

    Args:
      plugin_classes: A dictionary containing the plugin classes with
                      their class name as the key.
      platform: A string containing the supported operating system
                of the plugin.
      weight: An integer containing the weight of the plugin.

    Yields:
      Preprocess plugin objects (instance of PreprocessPlugin) that
      match the specified platform and weight.
    """
    for plugin_class in iter(plugin_classes.values()):
      plugin_supported_os = getattr(plugin_class, u'SUPPORTED_OS', [])
      plugin_weight = getattr(plugin_class, u'WEIGHT', 0)
      if platform in plugin_supported_os and weight == plugin_weight:
        yield plugin_class()

  @classmethod
  def _GetWeights(cls, plugin_classes, platform):
    """Returns a list of all weights that are used by preprocessing plugins.

    Args:
      plugin_classes: A dictionary containing the plugin classes with
                      their class name as the key.
      platform: A string containing the supported operating system
                of the plugin.

    Returns:
      A list of weights.
    """
    weights = {}
    for plugin_class in iter(plugin_classes.values()):
      plugin_supported_os = getattr(plugin_class, u'SUPPORTED_OS', [])
      plugin_weight = getattr(plugin_class, u'WEIGHT', 0)
      if platform in plugin_supported_os:
        weights[plugin_weight] = 1

    return sorted(weights.keys())

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters a plugin class.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
    """
    if (plugin_class.__name__ not in cls._plugin_classes and
        plugin_class.__name__ not in cls._registry_plugin_classes):
      raise KeyError(
          u'Plugin class not set for name: {0:s}.'.format(
              plugin_class.__name__))

    if plugin_class.__name__ in cls._plugin_classes:
      del cls._plugin_classes[plugin_class.__name__]

    if plugin_class.__name__ in cls._registry_plugin_classes:
      del cls._registry_plugin_classes[plugin_class.__name__]

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers a plugin class.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    if (plugin_class.__name__ in cls._plugin_classes or
        plugin_class.__name__ in cls._registry_plugin_classes):
      raise KeyError((
          u'Plugin class already set for name: {0:s}.').format(
              plugin_class.__name__))

    # TODO: use type check instead of check for KEY_PATH.
    if hasattr(plugin_class, u'KEY_PATH'):
      cls._registry_plugin_classes[plugin_class.__name__] = plugin_class
    else:
      cls._plugin_classes[plugin_class.__name__] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers a plugin classes.

    Args:
      plugin_classes: a list of class objects of the plugins.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)

  @classmethod
  def RunPlugins(cls, platform, file_system, mount_point, knowledge_base):
    """Runs the plugins for a specific platform.

    Args:
      platform: A string containing the supported operating system
                of the plugin.
      file_system: the file system object (instance of vfs.FileSystem)
                   to be preprocessed.
      mount_point: the mount point path specification (instance of
                   path.PathSpec) that refers to the base location
                   of the file system.
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    # TODO: bootstrap the artifact preprocessor.

    searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)

    for weight in cls._GetWeights(cls._plugin_classes, platform):
      for plugin_object in cls._GetPluginsByWeight(
          cls._plugin_classes, platform, weight):
        try:
          plugin_object.Run(searcher, knowledge_base)

        except (IOError, errors.PreProcessFail) as exception:
          logging.warning((
              u'Unable to run preprocessor: {0:s} for attribute: {1:s} '
              u'with error: {2:s}').format(
                  plugin_object.plugin_name, plugin_object.ATTRIBUTE,
                  exception))

    # Run the Registry plugins separately so we do not have to open
    # Registry files in every plugin.

    if knowledge_base:
      pre_obj = knowledge_base.pre_obj
      path_attributes = pre_obj.__dict__
    else:
      pre_obj = None
      path_attributes = None

    # TODO: do not pass the full pre_obj here but just
    # the necessary values.
    registry_file_reader = FileSystemWinRegistryFileReader(
        file_system, mount_point, path_attributes=path_attributes)
    win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)

    for weight in cls._GetWeights(cls._registry_plugin_classes, platform):
      for plugin_object in cls._GetPluginsByWeight(
          cls._registry_plugin_classes, platform, weight):

        try:
          plugin_object.Run(win_registry, knowledge_base)

        except (IOError, errors.PreProcessFail) as exception:
          logging.warning((
              u'Unable to run preprocessor: {0:s} for attribute: {1:s} '
              u'with error: {2:s}').format(
                  plugin_object.plugin_name, plugin_object.ATTRIBUTE,
                  exception))
