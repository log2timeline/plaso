# -*- coding: utf-8 -*-
"""This file contains the analysis plugin manager class."""

from plaso.analysis import definitions
from plaso.lib import errors


class AnalysisPluginManager(object):
  """Class that implements the analysis plugin manager."""

  _plugin_classes = {}

  _PLUGIN_TYPE_STRINGS = {
      definitions.PLUGIN_TYPE_ANNOTATION: (
          u'Annotation/Tagging plugin'),
      definitions.PLUGIN_TYPE_ANOMALY: (
          u'Anomaly plugin'),
      definitions.PLUGIN_TYPE_REPORT: (
          u'Summary/Report plugin'),
      definitions.PLUGIN_TYPE_STATISTICS: (
          u'Statistics plugin')
  }
  _PLUGIN_TYPE_STRINGS.setdefault(u'Unknown type')

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters an analysis plugin class.

    The analysis plugin classes are identified by their lower case name.

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
  def GetAllPluginInformation(cls, show_all=True):
    """Retrieves a list of the registered analysis plugins.

    Args:
      show_all: optional boolean value to indicate to list all the analysis
                plugin names.

    Returns:
      A sorted list of tuples containing the name, docstring and type string
      of each analysis plugin.
    """
    results = []
    for plugin_class in iter(cls._plugin_classes.values()):
      plugin_object = plugin_class(None)
      if not show_all and not plugin_class.ENABLE_IN_EXTRACTION:
        continue

      # TODO: Use a specific description variable, not the docstring.
      doc_string, _, _ = plugin_class.__doc__.partition(u'\n')
      type_string = cls._PLUGIN_TYPE_STRINGS.get(plugin_object.plugin_type)
      information_tuple = (plugin_object.plugin_name, doc_string, type_string)
      results.append(information_tuple)

    return sorted(results)

  @classmethod
  def LoadPlugins(cls, plugin_names, incoming_queues):
    """Yield analysis plugins for a given list of plugin names.

    Given a list of plugin names this method finds the analysis
    plugins, initializes them and returns a generator.

    Args:
      plugin_names: A list of plugin names that should be loaded up. This
                    should be a list of strings.
      incoming_queues: A list of queues (instances of QueueInterface) that
                       the plugin uses to read in incoming events to analyse.

    Yields:
      Analysis plugin objects (instances of AnalysisPlugin).

    Raises:
      errors.BadConfigOption: If plugins_names does not contain a list of
                              strings.
    """
    try:
      plugin_names_lower = [word.lower() for word in plugin_names]
    except AttributeError:
      raise errors.BadConfigOption(u'Plugin names should be a list of strings.')

    for plugin_object in iter(cls._plugin_classes.values()):
      plugin_name = plugin_object.NAME.lower()

      if plugin_name in plugin_names_lower:
        queue_index = plugin_names_lower.index(plugin_name)

        try:
          incoming_queue = incoming_queues[queue_index]
        except (TypeError, IndexError):
          incoming_queue = None

        yield plugin_object(incoming_queue)

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
