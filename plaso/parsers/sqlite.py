#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a SQLite parser."""

import logging

import sqlite3

from plaso.lib import errors
from plaso.parsers import interface
# Register sqlite plugins.
from plaso.parsers import sqlite_plugins  # pylint: disable=unused-import
from plaso.parsers import manager
from plaso.parsers.sqlite_plugins import interface as sqlite_plugins_interface


class SQLiteParser(interface.BaseParser):
  """A SQLite parser for Plaso."""

  # Name of the parser, which enables all plugins by default.
  NAME = 'sqlite'

  def __init__(self):
    """Initializes a parser object."""
    super(SQLiteParser, self).__init__()
    self._local_zone = False
    self.db = None
    self._plugins = manager.ParsersManager.GetRegisteredPlugins(
        parent_class=sqlite_plugins_interface.SQLitePlugin)

  def Parse(self, parser_context, file_entry):
    """Parses an SQLite database.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A event object generator (EventObjects) extracted from the database.
    """
    with sqlite_plugins_interface.SQLiteDatabase(file_entry) as database:
      try:
        database.Open()
      except IOError as exception:
        raise errors.UnableToParseFile(
            u'Unable to open database with error: {0:s}'.format(
                repr(exception)))
      except sqlite3.DatabaseError as exception:
        raise errors.UnableToParseFile(
            u'Unable to parse SQLite database with error: {0:s}.'.format(
                repr(exception)))

      # Create a cache in which the resulting tables are cached.
      cache = sqlite_plugins_interface.SQLiteCache()
      for plugin_object in self._plugins.itervalues():
        try:
          plugin_object.Process(parser_context, cache=cache, database=database)

        except errors.WrongPlugin:
          logging.debug(
              u'Plugin: {0:s} cannot parse database: {1:s}'.format(
                  plugin_object.plugin_name, file_entry.name))
