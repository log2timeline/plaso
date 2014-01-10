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

from plaso.lib import errors
from plaso.lib import parser
from plaso.lib import plugin

from plaso.parsers.sqlite_plugins import interface

# Register all sqlite plugins.
# pylint: disable-msg=unused-import
from plaso.parsers import sqlite_plugins

import sqlite3


class SQLiteParser(parser.BaseParser):
  """A SQLite parser for Plaso."""

  # Name of the parser, which enables all plugins by default.
  NAME = 'sqlite'

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(SQLiteParser, self).__init__(pre_obj, config)
    self._local_zone = False
    self.db = None
    parser_filter_string = getattr(self._config, 'parsers', None)

    self._plugins = plugin.GetRegisteredPlugins(
        interface.SQLitePlugin, self._pre_obj, parser_filter_string)

  def Parse(self, file_entry):
    """Parses an SQLite database.

    Args:
      file_entry: the file entry object.

    Returns:
      A event object generator (EventObjects) extracted from the database.
    """
    with interface.SQLiteDatabase(file_entry) as database:
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

      # Reset potential cache.
      for plugin_obj in self._plugins.itervalues():
        try:
          for event_object in plugin_obj.Process(database):
            event_object.plugin = plugin_obj.plugin_name
            yield event_object
        except errors.WrongPlugin:
          logging.debug(
              u'Plugin: {0:s} cannot parse database: {1:s}'.format(
                  plugin_obj.plugin_name, file_entry.name))

