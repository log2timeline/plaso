#!/usr/bin/python
# -*- coding: utf-8 -*-
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


class SQLiteParser(parser.PlasoParser):
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
    self._plugins = self._GetPlugins()

  def _GetPlugins(self):
    """Return a list of all available plugins."""
    parser_filter_string = getattr(self._config, 'parsers', None)

    return plugin.GetRegisteredPlugins(
        interface.SQLitePlugin, self._pre_obj, parser_filter_string)

  def Parse(self, filehandle):
    """Return a generator for EventObjects extracted from SQLite db."""
    with interface.SQLiteDatabase(filehandle) as database:
      try:
        database.Open()
      except IOError as e:
        raise errors.UnableToParseFile(
            u'Not able to open database: {}'.format(e))
      except sqlite3.DatabaseError as e:
        raise errors.UnableToParseFile(
            u'Unable to parse SQLite database due to an error: %s.' % e)

      for plugin_obj in self._plugins.itervalues():
        try:
          for event_object in plugin_obj.Process(database):
            yield event_object
        except errors.WrongPlugin:
          logging.debug(u'Unable to parse database: {} using {}'.format(
              filehandle.name, plugin_obj.plugin_name))

