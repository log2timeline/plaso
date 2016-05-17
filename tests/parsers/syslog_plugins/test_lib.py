# -*- coding: utf-8 -*-
"""Syslog plugin related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import single_process

from plaso.parsers import syslog

from tests.parsers import test_lib


class SyslogPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for Syslog plugins."""

  def _ParseFileWithPlugin(
      self, plugin_name, path, knowledge_base_values=None):
    """Parses a syslog file with a specific plugin.

    Args:
      plugin_name: a string containing the name of the plugin.
      path: a string containing the path to the syslog file.
      knowledge_base_values: optional dictionary containing the knowledge base
                             values.

    Returns:
      An event object queue consumer object (instance of ItemQueueConsumer).
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

    parser_object = syslog.SyslogParser()
    parser_object.EnablePlugins([plugin_name])

    file_object = file_entry.GetFileObject()
    try:
      parser_object.Parse(parser_mediator, file_object)
    finally:
      file_object.close()

    return event_queue_consumer
