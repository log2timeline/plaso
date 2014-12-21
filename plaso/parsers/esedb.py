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
"""Parser for Extensible Storage Engine (ESE) database files (EDB)."""

import logging

import pyesedb

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins


if pyesedb.get_version() < '20140301':
  raise ImportWarning(u'EseDbParser requires at least pyesedb 20140301.')


class EseDbCache(plugins.BasePluginCache):
  """A cache storing query results for ESEDB plugins."""

  def StoreDictInCache(self, attribute_name, dict_object):
    """Store a dict object in cache.

    Args:
      attribute_name: The name of the attribute.
      dict_object: A dict object.
    """
    setattr(self, attribute_name, dict_object)


class EseDbParser(interface.BasePluginsParser):
  """Parses Extensible Storage Engine (ESE) database files (EDB)."""

  NAME = 'esedb'
  DESCRIPTION = u'Parser for Extensible Storage Engine (ESE) database files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(EseDbParser, self).__init__()
    self._plugins = EseDbParser.GetPluginObjects()

  def Parse(self, parser_context, file_entry, parser_chain=None):
    """Extracts data from an ESE database File.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object = file_entry.GetFileObject()
    esedb_file = pyesedb.file()

    try:
      esedb_file.open_file_object(file_object)
    except IOError as exception:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.NAME, file_entry.name, exception))

    # Add ourselves to the parser chain, which will be used in all subsequent
    # event creation in this parser.
    parser_chain = self._BuildParserChain(parser_chain)

    # Compare the list of available plugins.
    cache = EseDbCache()
    for plugin_object in self._plugins:
      try:
        plugin_object.Process(
            parser_context, file_entry=file_entry, parser_chain=parser_chain,
            database=esedb_file, cache=cache)

      except errors.WrongPlugin:
        logging.debug((
            u'[{0:s}] plugin: {1:s} cannot parse the ESE database: '
            u'{2:s}').format(
                self.NAME, plugin_object.NAME, file_entry.name))

    # TODO: explicitly clean up cache.

    esedb_file.close()
    file_object.close()


manager.ParsersManager.RegisterParser(EseDbParser)
