#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Import statements for analysis plugins and common methods."""

from plaso.analysis import interface
from plaso.lib import errors

# Import statements of analysis plugins.
from plaso.analysis import browser_search
from plaso.analysis import chrome_extension
from plaso.analysis import windows_services


# TODO: move these functions to a manager class. And add a test for this
# function.
def ListAllPluginNames(show_all=True):
  """Return a list of all available plugin names and it's doc string."""
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
