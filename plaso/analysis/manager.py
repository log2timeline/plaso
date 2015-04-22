# -*- coding: utf-8 -*-
"""This file contains the analysis plugin manager class."""

from plaso.analysis import interface
from plaso.lib import errors


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
  def ListAllPluginNames(cls, show_all=True):
    """Retrieves a list of the registered analysis plugins.

    Args:
      show_all: optional boolean value to indicate to list all the analysis
                plugin names. The default is True.

    Returns:
      A sorted lists of available plugin names and their docstrings.
    """
    results = []
    for cls_obj in interface.AnalysisPlugin.classes.itervalues():
      doc_string, _, _ = cls_obj.__doc__.partition(u'\n')

      obj = cls_obj(None)
      if show_all or cls_obj.ENABLE_IN_EXTRACTION:
        results.append((obj.plugin_name, doc_string, obj.plugin_type))

    return sorted(results)

  # TODO: refactor options out of function.
  @classmethod
  def LoadPlugins(cls, plugin_names, incoming_queues, options=None):
    """Yield analysis plugins for a given list of plugin names.

    Given a list of plugin names this method finds the analysis
    plugins, initializes them and returns a generator.

    Args:
      plugin_names: A list of plugin names that should be loaded up. This
                    should be a list of strings.
      incoming_queues: A list of queues (instances of QueueInterface) that
                       the plugin uses to read in incoming events to analyse.
      options: Optional command line arguments (instance of
               argparse.Namespace). The default is None.

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

    for plugin_object in interface.AnalysisPlugin.classes.itervalues():
      plugin_name = plugin_object.NAME.lower()

      if plugin_name in plugin_names_lower:
        queue_index = plugin_names_lower.index(plugin_name)

        try:
          incoming_queue = incoming_queues[queue_index]
        except (TypeError, IndexError):
          incoming_queue = None

        yield plugin_object(incoming_queue, options)

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
