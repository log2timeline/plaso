#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""SQLite database plugin related functions and classes for testing."""

from plaso.parsers import test_lib
from plaso.parsers.sqlite_plugins import interface as sqlite_interface
from plaso.pvfs import pfile


class SQLitePluginTestCase(test_lib.ParserTestCase):
  """The unit test case for SQLite database plugins."""

  def _ParseDatabaseFileWithPlugin(self, plugin_object, path, cache=None):
    """Parses a file as a SQLite database and returns an event generator.

    Args:
      plugin_object: The plugin object that is used to extract an event
                     generator.
      path: The path to the SQLite database file.
      cache: A cache object (instance of SQLiteCache).

    Returns:
      A generator of event objects as returned by the plugin.
    """
    path_spec = pfile.PFileResolver.CopyPathToPathSpec('OS', path)
    file_entry = pfile.PFileResolver.OpenFileEntry(path_spec)
    with sqlite_interface.SQLiteDatabase(file_entry) as database:
      event_generator = plugin_object.Process(cache=cache, database=database)

    self.assertNotEquals(event_generator, None)

    return event_generator
