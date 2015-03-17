# -*- coding: utf-8 -*-
"""Import statements for analysis plugins and common methods."""

from plaso.analysis import interface
from plaso.lib import errors

# Import statements of analysis plugins.
from plaso.analysis import browser_search
from plaso.analysis import chrome_extension
from plaso.analysis import file_hashes
from plaso.analysis import windows_services


# TODO: move these functions to a manager class. And add a test for this
# function.
def ListAllPluginNames(show_all=True):
  """Return a list of all available plugin names and their docstrings."""
  results = []
  for cls_obj in interface.AnalysisPlugin.classes.itervalues():
    doc_string, _, _ = cls_obj.__doc__.partition('\n')

    obj = cls_obj(None)
    if not show_all and cls_obj.ENABLE_IN_EXTRACTION:
      results.append((obj.plugin_name, doc_string, obj.plugin_type))
    elif show_all:
      results.append((obj.plugin_name, doc_string, obj.plugin_type))

  return sorted(results)


def LoadPlugins(plugin_names, incoming_queues, options=None):
  """Yield analysis plugins for a given list of plugin names.

  Given a list of plugin names this method finds the analysis
  plugins, initializes them and returns a generator.

  Args:
    plugin_names: A list of plugin names that should be loaded up. This
                  should be a list of strings.
    incoming_queues: A list of queues (QueueInterface object) that the plugin
                     uses to read in incoming events to analyse.
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
