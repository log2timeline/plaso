# -*- coding: utf-8 -*-
"""This file contains the analysis plugin manager class."""

from plaso.analysis import definitions


class AnalysisPluginManager(object):
  """Analysis plugin manager."""

  _plugin_classes = {}

  _PLUGIN_TYPE_STRINGS = {
      definitions.PLUGIN_TYPE_ANNOTATION: (
          'Annotation/Tagging plugin'),
      definitions.PLUGIN_TYPE_ANOMALY: (
          'Anomaly plugin'),
      definitions.PLUGIN_TYPE_REPORT: (
          'Summary/Report plugin'),
      definitions.PLUGIN_TYPE_STATISTICS: (
          'Statistics plugin')
  }
  _PLUGIN_TYPE_STRINGS.setdefault('Unknown type')

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters an analysis plugin class.

    The analysis plugin classes are identified by their lower case name.

    Args:
      plugin_class (type): class of the analysis plugin.

    Raises:
      KeyError: if an analysis plugin class is not set for the corresponding
          name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name not in cls._plugin_classes:
      raise KeyError('Plugin class not set for name: {0:s}.'.format(
          plugin_class.NAME))

    del cls._plugin_classes[plugin_name]

  # TODO: refactor to match parsers manager.
  @classmethod
  def GetAllPluginInformation(cls):
    """Retrieves a list of the registered analysis plugins.

    Returns:
      list[tuple[str, str, str]]: the name, docstring and type string of each
          analysis plugin in alphabetical order.
    """
    results = []
    for plugin_class in cls._plugin_classes.values():
      if not plugin_class.TEST_PLUGIN:
        plugin_object = plugin_class()
        # TODO: Use a specific description variable, not the docstring.
        doc_string, _, _ = plugin_class.__doc__.partition('\n')
        type_string = cls._PLUGIN_TYPE_STRINGS.get(plugin_object.plugin_type)
        information_tuple = (plugin_object.NAME, doc_string, type_string)
        results.append(information_tuple)

    return sorted(results)

  @classmethod
  def GetPluginNames(cls):
    """Retrieves the analysis  plugin names.

    Returns:
      list[str]: analysis plugin names.
    """
    return sorted(cls._plugin_classes.keys())

  @classmethod
  def GetPluginObjects(cls, plugin_names):
    """Retrieves the plugin objects.

    Args:
      plugin_names (list[str]): names of plugins that should be retrieved.

    Returns:
      dict[str, AnalysisPlugin]: analysis plugins per name.
    """
    plugin_objects = {}
    for plugin_name, plugin_class in cls._plugin_classes.items():
      if plugin_name not in plugin_names:
        continue

      plugin_objects[plugin_name] = plugin_class()

    return plugin_objects

  @classmethod
  def GetPlugins(cls):
    """Retrieves the registered analysis plugin classes.

    Yields:
      tuple: containing:

        str: name of the plugin
        type: plugin class
    """
    for plugin_name, plugin_class in cls._plugin_classes.items():
      yield plugin_name, plugin_class

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers an analysis plugin class.

    Then analysis plugin classes are identified based on their lower case name.

    Args:
      plugin_class (type): class of the analysis plugin.

    Raises:
      KeyError: if an analysis plugin class is already set for the corresponding
          name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name in cls._plugin_classes:
      raise KeyError('Plugin class already set for name: {0:s}.'.format(
          plugin_class.NAME))

    cls._plugin_classes[plugin_name] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers analysis plugin classes.

    The analysis plugin classes are identified based on their lower case name.

    Args:
      plugin_classes (list[type]): classes of the analysis plugin.

    Raises:
      KeyError: if an analysis plugin class is already set for the corresponding
          name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)
