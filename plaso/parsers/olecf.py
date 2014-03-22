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
"""Parser for OLE Compound Files (OLECF)."""

import logging

from plaso.lib import errors
from plaso.lib import parser
from plaso.lib import plugin

from plaso.parsers.olecf_plugins import interface

# Register all OLECF plugins.
# pylint: disable-msg=unused-import
from plaso.parsers import olecf_plugins

import pyolecf


if pyolecf.get_version() < '20131012':
  raise ImportWarning('OleCfParser requires at least pyolecf 20131012.')


class OleCfParser(parser.BaseParser):
  """Parses OLE Compound Files (OLECF)."""

  NAME = 'olecf'

  def __init__(self, pre_obj, config=None):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(OleCfParser, self).__init__(pre_obj, config)
    self._codepage = getattr(self._pre_obj, 'codepage', 'cp1252')
    parser_filter_string = getattr(self._config, 'parsers', None)

    self._plugins = plugin.GetRegisteredPlugins(
        interface.OlecfPlugin, self._pre_obj, parser_filter_string)

  def Parse(self, file_entry):
    """Extracts data from an OLE Compound File (OLECF).

    Args:
      file_entry: A file entry object.

    Yields:
      An event container (EventContainer) that contains the parsed
      attributes.
    """
    file_object = file_entry.GetFileObject()
    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(self._codepage)

    try:
      olecf_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.parser_name, file_entry.name, exception))

    # Get a list of all root items from the OLE CF file.
    root_item = olecf_file.root_item
    item_names = [item.name for item in root_item.sub_items]

    # Compare the list of available plugins.
    # We will try to use every plugin against the file (except
    # the default plugin) and run it. Only if none of the plugins
    # works will we use the default plugin.
    parsed = False
    for olecf_name, olecf_plugin in self._plugins.iteritems():
      # We would like to skip the default plugin for now.
      if olecf_name == 'olecf_default':
        continue
      try:
        for event_object in olecf_plugin.Process(
            root_item=root_item, item_names=item_names):
          parsed = True
          event_object.plugin = olecf_plugin.plugin_name
          yield event_object
      except errors.WrongPlugin:
        logging.debug(
            u'Plugin: {:s} cannot parse the OLECF file: {:s}'.format(
                olecf_plugin.plugin_name, file_entry.name))

    # Check if we still haven't parsed the file, and if so we will use
    # the default OLECF plugin.
    if not parsed:
      default_plugin = self._plugins.get('olecf_default', None)
      if default_plugin:
        for event_object in default_plugin.Process(
            root_item=root_item, item_names=item_names):
          event_object.plugin = default_plugin.plugin_name
          yield event_object

    file_object.close()
