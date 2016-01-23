# -*- coding: utf-8 -*-
"""Bencode plugin related functions and classes for testing."""

from tests.parsers import test_lib


class BencodePluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a bencode plugin."""

  def _GetEventObjectsFromQueue(self, event_queue_consumer):
    """Retrieves the event objects from the queue consumer.

    Args:
      event_queue_consumer: an event object queue consumer object (instance of
                            TestItemQueueConsumer).

    Returns:
      A list of event objects (instances of EventObject).
    """
    # The inner workings of bencode does not provide a predictable order
    # of events. Hence sort the resulting event objects to make sure they are
    # predicatable for the tests.
    event_objects = super(
        BencodePluginTestCase, self)._GetEventObjectsFromQueue(
            event_queue_consumer)
    return sorted(
        event_objects, key=lambda event_object: event_object.timestamp)
