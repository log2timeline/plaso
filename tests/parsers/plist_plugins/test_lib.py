# -*- coding: utf-8 -*-
"""Plist plugin related functions and classes for testing."""

from plaso.engine import single_process

from tests.parsers import test_lib


class PlistPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a plist plugin."""

  def _GetEventObjectsFromQueue(self, event_queue_consumer):
    """Retrieves the event objects from the queue consumer.

    Args:
      event_queue_consumer: an event object queue consumer object (instance of
                            TestItemQueueConsumer).

    Returns:
      A list of event objects (instances of EventObject).
    """
    # The inner workings of binplist does not provide a predictable order
    # of events. Hence sort the resulting event objects to make sure they are
    # predicatable for the tests.
    event_objects = super(PlistPluginTestCase, self)._GetEventObjectsFromQueue(
        event_queue_consumer)
    return sorted(
        event_objects, key=lambda event_object: event_object.timestamp)

  def _ParsePlistFileWithPlugin(
      self, parser_object, plugin_object, path_segments, plist_name,
      knowledge_base_values=None):
    """Parses a file using the parser and plugin object.

    Args:
      parser_object: the parser object.
      plugin_object: the plugin object.
      path_segments: the path segments inside the test data directory to the
                     test file.
      plist_name: the name of the plist to parse.
      knowledge_base_values: optional dict containing the knowledge base
                             values.

    Returns:
      An event object queue consumer object (instance of
      TestItemQueueConsumer).
    """
    file_entry = self._GetTestFileEntryFromPath(path_segments)
    file_object = file_entry.GetFileObject()
    top_level_object = parser_object.GetTopLevel(file_object)
    self.assertIsNotNone(top_level_object)

    return self._ParsePlistWithPlugin(
        plugin_object, plist_name, top_level_object,
        knowledge_base_values=knowledge_base_values)

  def _ParsePlistWithPlugin(
      self, plugin_object, plist_name, top_level_object,
      knowledge_base_values=None):
    """Parses a plist using the plugin object.

    Args:
      plugin_object: the plugin object.
      plist_name: the name of the plist to parse.
      top_level_object: the top-level plist object.
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

    plugin_object.Process(
        parser_mediator, plist_name=plist_name, top_level=top_level_object)

    return event_queue_consumer
