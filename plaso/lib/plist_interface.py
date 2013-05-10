#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""This file contains basic interface for plist handling within Plaso."""

import abc
import logging

from plaso.lib import errors
from plaso.lib import registry


class PlistPlugin(object):
  """Plist plugin takes a property list and extracts entries from it.

  The entries that are extracted are in the form of an EventObject that
  describes the content of the key in a human readable format.
  """

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # PLIST_PATH is a string for the filename this parser is designed to process.
  # This is expected to be overriden by the processing plugin.
  PLIST_PATH = 'any'

  # PLIST_KEYS is a list of keys required by a plugin.
  # This is expected to be overriden by the processing plugin.
  PLIST_KEYS = frozenset(['any'])

  # The URLS should contain a list of URL's with additional information about
  # this key or value.
  URLS = []

  def __init__(self, pre_obj):
    """Constructor for a plist plugin.

    Args:
      pre_obj: This is a PlasoPreprocess object.
    """
    self._config = pre_obj

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.__class__.__name__

  @abc.abstractmethod
  def GetEntries(self):
    """Extract and return EventObjects from the plist key."""

  def __iter__(self):
    for entry in self.GetEntries():
      yield entry

  def Process(self, plist_name, top_level):
    """Determine if this is the correct plugin; if so proceed with processing.

    This function also extracts the required keys as defined in self.PLIST_KEYS
    from the serialized plist and stores the result in self.match[key].

    Args:
      plist_name: Name of the plist file.
      top_level: Contents of a plist serialized.

    Raises:
      WrongPlistPlugin: If this plugin is not able to process the given file.

    Returns:
      A generator of events processed by the plugin.
    """
    self._top_level = top_level

    if not plist_name.lower() == self.PLIST_PATH.lower():
      raise errors.WrongPlistPlugin(self.plugin_name, plist_name)

    if set(top_level.keys()) >= self.PLIST_KEYS:
      logging.debug('Plist Plugin Used: {} for: {}'.format(self.plugin_name,
                                                           plist_name))
      self.match = GetKeys(top_level, self.PLIST_KEYS)
      return self.GetEntries()

    raise errors.WrongPlistPlugin(self.plugin_name, plist_name)


def RecurseKey(recur_item, root='', depth=15):
  """Recurse through nested dictionaries yielding non-dictionary values.

  Args:
    recur_item: An object to be checked for additional nested items.
    root: The pathname of the current working key.
    depth: A counter to ensure we stop at the maximum recursion depth.

  Yields:
    A tuple of the root, key, and value from a plist.
  """
  if depth < 1:
    logging.warning(
        u'Recursion limit hit for key: %s', root)
    return

  if not isinstance(recur_item, dict):
    for value in recur_item:
      yield root, '', value
  else:
    for key, value in recur_item.iteritems():
      yield root, key, value
      if isinstance(value, dict):
        for keyval in RecurseKey(
            value, root=u'/'.join([root, key]), depth=depth - 1):
          yield keyval
      if isinstance(value, list):
        for item in value:
          if isinstance(item, dict):
            for keyval in RecurseKey(
                item, root=u'/'.join([root, key]), depth=depth - 1):
              yield keyval


def GetKeys(top_level, keys):
  """Helper function to return keys nested in a plist dict.

  Args:
    top_level: A serialized plist file.
    keys: A list of keys that should be returned.

  Returns:
    A dictionary with just the keys requested.
  """
  match = {}
  for _, parsed_key, parsed_value in RecurseKey(top_level):
    if parsed_key in keys:
      match[parsed_key] = parsed_value
  return match


def GetPlistPlugins(pre_obj=None):
  """Build a list of all available plugins capable of parsing the plist files.

  This method uses the class registration library to find all classes that have
  implemented the PlistPlugin class and compiles a list of plugin objects.

  Args:
    pre_obj: A PlasoPreprocess object containing information.

  Returns:
    A list of plist plugin objects.
  """

  plugins = []

  for plugin_cls in PlistPlugin.classes.values():
    plugins.append(plugin_cls(pre_obj))

  return plugins
