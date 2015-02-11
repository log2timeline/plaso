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

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import single_process
from plaso.parsers import sqlite
from plaso.parsers import test_lib


class SQLitePluginTestCase(test_lib.ParserTestCase):
  """The unit test case for SQLite database plugins."""

  def _ParseDatabaseFileWithPlugin(
      self, plugin_object, path, cache=None, knowledge_base_values=None):
    """Parses a file as a SQLite database with a specific plugin.

    Args:
      plugin_object: The plugin object that is used to extract an event
                     generator.
      path: The path to the SQLite database file.
      cache: A cache object (instance of SQLiteCache).
      knowledge_base_values: optional dict containing the knowledge base
                             values. The default is None.

    Returns:
      An event object queue consumer object (instance of
      TestEventObjectQueueConsumer).
    """
    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = test_lib.TestEventObjectQueueConsumer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()

    parser_mediator = self._GetParserMediator(
        event_queue, parse_error_queue,
        knowledge_base_values=knowledge_base_values)
    parser_mediator.AppendToParserChain(plugin_object)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    parser_mediator.SetFileEntry(file_entry)

    with sqlite.SQLiteDatabase(file_entry) as database:
      plugin_object.Process(parser_mediator, cache=cache, database=database)

    return event_queue_consumer
