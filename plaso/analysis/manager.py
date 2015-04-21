# -*- coding: utf-8 -*-
"""This file contains the analysis plugin manager class."""


class AnalysisPluginManager(object):
  """Class that implements the analysis plugin manager."""

  _plugin_classes = {}

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters an analysis plugin class.

    The anlysis plugin classes are identified based on their lower case name.

    Args:
      plugin_class: the class object of the analysis plugin.

    Raises:
      KeyError: if analysis plugin class is not set for the corresponding name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name not in cls._plugin_classes:
      raise KeyError(u'Plugin class not set for name: {0:s}.'.format(
          plugin_class.NAME))

    del cls._plugin_classes[plugin_name]

  @classmethod
  def GetPlugins(cls):
    """Retrieves the registered analysis plugin classes.

    Yields:
      A tuple that contains the uniquely identifying name of the plugin
      and the plugin class (subclass of AnalysisPlugin).
    """
    for plugin_name, plugin_class in cls._plugin_classes.iteritems():
      yield plugin_name, plugin_class

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers an analysis plugin class.

    Then analysis plugin classes are identified based on their lower case name.

    Args:
      plugin_class: the class object of the analysis plugin.

    Raises:
      KeyError: if analysis plugin class is already set for the corresponding
                name.
    """
    plugin_name = plugin_class.NAME.lower()
    if plugin_name in cls._plugin_classes:
      raise KeyError(u'Plugin class already set for name: {0:s}.'.format(
          plugin_class.NAME))

    cls._plugin_classes[plugin_name] = plugin_class

  @classmethod
  def RegisterPlugins(cls, plugin_classes):
    """Registers formatter classes.

    The formatter classes are identified based on their lower case name.

    Args:
      plugin_classes: a list of class objects of the formatters.

    Raises:
      KeyError: if formatter class is already set for the corresponding name.
    """
    for plugin_class in plugin_classes:
      cls.RegisterPlugin(plugin_class)
