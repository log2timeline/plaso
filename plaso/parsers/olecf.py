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

import pyolecf

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


if pyolecf.get_version() < '20131012':
  raise ImportWarning('OleCfParser requires at least pyolecf 20131012.')


class OleCfParser(interface.BasePluginsParser):
  """Parses OLE Compound Files (OLECF)."""

  NAME = 'olecf'
  DESCRIPTION = u'Parser for OLE Compound Files (OLECF).'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(OleCfParser, self).__init__()
    self._plugins = OleCfParser.GetPluginObjects()

    for list_index, plugin_object in enumerate(self._plugins):
      if plugin_object.NAME == 'olecf_default':
        self._default_plugin = self._plugins.pop(list_index)
        break

  def Parse(self, parser_context, file_entry):
    """Extracts data from an OLE Compound File (OLECF).

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      Event objects (EventObject) that contains the parsed
      attributes.
    """
    file_object = file_entry.GetFileObject()
    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(parser_context.codepage)

    try:
      olecf_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, file_entry.name, exception))

    # Get a list of all root items from the OLE CF file.
    root_item = olecf_file.root_item
    item_names = [item.name for item in root_item.sub_items]

    # Compare the list of available plugins.
    # We will try to use every plugin against the file (except
    # the default plugin) and run it. Only if none of the plugins
    # works will we use the default plugin.
    parsed = False
    for plugin_object in self._plugins:
      try:
        plugin_object.Process(
            parser_context, file_entry=file_entry, root_item=root_item,
            item_names=item_names)

      except errors.WrongPlugin:
        logging.debug(
            u'[{0:s}] plugin: {1:s} cannot parse the OLECF file: {2:s}'.format(
                self.NAME, plugin_object.NAME, file_entry.name))

    # Check if we still haven't parsed the file, and if so we will use
    # the default OLECF plugin.
    if not parsed and self._default_plugin:
      self._default_plugin.Process(
          parser_context, file_entry=file_entry, root_item=root_item,
          item_names=item_names)

    olecf_file.close()
    file_object.close()


manager.ParsersManager.RegisterParser(OleCfParser)
