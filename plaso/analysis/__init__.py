#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from plaso.lib import analysis_interface
from plaso.lib import errors


def ListAllPluginNames():
  """Return a list of all available plugin names."""
  results = []
  for cls_obj in analysis_interface.AnalysisPlugin.classes:
    results.append(analysis_interface.AnalysisPlugin.classes[cls_obj](
        None, None).plugin_name)

  return sorted(results)


def LoadPlugins(plugin_names, pre_obj, incoming_queue):
  """Yield analysis plugins for a given list of plugin names.

  Given a list of plugin names this method finds the analysis
  plugins, initializes them and returns a generator.

  Args:
    plugin_names: A list of plugin names that should be loaded up. This
                  shold be a list of strings.
    pre_obj: The pre-processing object.
    incoming_queue: A queue (QueueInterface object) that the plugin
                    uses to read in incoming events to analyse.

  Yields:
    A list of initialized analysis plugin objects.

  Raises:
    errors.BadConfigOption: If plugins_names does not contain a list of
                            strings.
  """
  try:
    plugin_names_lower = [word.lower() for word in plugin_names]
  except AttributeError:
    raise errors.BadConfigOption(u'Plugin names should be a list of strings.')

  for name, obj in analysis_interface.AnalysisPlugin.classes.items():
    if name.lower() in plugin_names_lower:
      yield obj(pre_obj, incoming_queue)
