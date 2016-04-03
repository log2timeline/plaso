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

  def _RemoveOtherPluginsFromParser(self, plugin_object):
    """Removes unrelated the plugins from the syslog parser.

    The parser will load only the specified plugin.

    Args:
      plugin_object: The plugin object to be used.

    Returns:
      The parsers that were unregistered from the syslog parser.
    """
    # We need to save the classes we want to remove as we go, as we can't
    # modify the plugin list while iterating over it in GetPlugins().
    classes_to_remove = []
    for plugin_name, plugin_class in syslog.SyslogParser.GetPlugins():
      if plugin_name != plugin_object.NAME:
        classes_to_remove.append(plugin_class)
    for plugin_class in classes_to_remove:
      syslog.SyslogParser.DeregisterPlugin(plugin_class)
    return classes_to_remove

  def _ParseFileWithPlugin(
      self, plugin_object, path, knowledge_base_values=None):
    """Parses a syslog file with a specific plugin.

    Args:
      plugin_object: The plugin object that is used to extract an event
                     generator.
      path: The path to the syslog file.
      knowledge_base_values: optional dict containing the knowledge base
                             values.

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

    parser = syslog.SyslogParser()
    removed_plugins = self._RemoveOtherPluginsFromParser(plugin_object)
    try:
      parser.Parse(parser_mediator, file_entry.GetFileObject())
    finally:
      syslog.SyslogParser.RegisterPlugins(removed_plugins)

    return event_queue_consumer
