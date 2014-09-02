#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Parser for Extensible Storage Engine (ESE) database Files (EDB)."""

import logging

import pyesedb

from plaso.lib import errors
# Register all ESEDB plugins.
from plaso.parsers import esedb_plugins  # pylint: disable=unused-import
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers.esedb_plugins import interface as esedb_plugins_interface


if pyesedb.get_version() < '20140301':
  raise ImportWarning(u'EseDbParser requires at least pyesedb 20140301.')


class EseDbParser(interface.BaseParser):
  """Parses Extensible Storage Engine (ESE) database Files (EDB)."""

  NAME = 'esedb'

  def __init__(self):
    """Initializes a parser object."""
    super(EseDbParser, self).__init__()
    self._plugins = manager.ParsersManager.GetRegisteredPlugins(
        parent_class=esedb_plugins_interface.EseDbPlugin)

  def Parse(self, parser_context, file_entry):
    """Extracts data from an ESE database File.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Yields:
      An event event (instance of EventObject) that contains the parsed
      values.
    """
    file_object = file_entry.GetFileObject()
    esedb_file = pyesedb.file()

    try:
      esedb_file.open_file_object(file_object)
    except IOError as exception:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.parser_name, file_entry.name, exception))

    # Compare the list of available plugins.
    cache = esedb_plugins_interface.EseDbCache()
    for esedb_plugin in self._plugins.itervalues():
      try:
        esedb_plugin.Process(
            parser_context, database=esedb_file, cache=cache)

      except errors.WrongPlugin:
        logging.debug((
            u'[{0:s}] plugin: {1:s} cannot parse the ESE database: '
            u'{2:s}').format(
                self.parser_name, esedb_plugin.plugin_name, file_entry.name))

    # TODO: explicitly clean up cache.

    file_object.close()
