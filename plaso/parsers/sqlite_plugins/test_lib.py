# -*- coding: utf-8 -*-
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
      TestItemQueueConsumer).
    """
    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = test_lib.TestItemQueueConsumer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()

    parser_mediator = self._GetParserMediator(
        event_queue, parse_error_queue,
        knowledge_base_values=knowledge_base_values)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    parser_mediator.SetFileEntry(file_entry)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain(plugin_object)

    with sqlite.SQLiteDatabase(file_entry) as database:
      plugin_object.Process(parser_mediator, cache=cache, database=database)

    return event_queue_consumer
