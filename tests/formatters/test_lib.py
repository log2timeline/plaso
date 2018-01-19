# -*- coding: utf-8 -*-
"""Event formatter related functions and classes for testing."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import interface
from plaso.formatters import mediator

from tests.containers import test_lib as container_test_lib


class TestEventFormatter(interface.EventFormatter):
  """Test event formatter."""

  DATA_TYPE = 'test:event'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'FILE'
  SOURCE_LONG = 'Weird Log File'


class EventFormatterTestCase(unittest.TestCase):
  """The unit test case for an event formatter."""

  def _MakeTestEvent(self, event_data):
    """Creates a test event containing the provided data.

    Args:
      event_data (EventData): event data.

    Returns:
      TestEvent: a test event.
    """
    attributes = event_data.CopyToDict()
    event = container_test_lib.TestEvent(1, attributes)
    return event

  def _TestGetFormatStringAttributeNames(
      self, event_formatter, expected_attribute_names):
    """Tests the GetFormatStringAttributeNames function.

    Args:
      event_formatter (EventFormatter): event formatter under test.
      expected_attribute_names (list[str]): expected attribute names.
    """
    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), sorted(expected_attribute_names))

  def _TestGetMessages(
      self, event, formatter, expected_message, expected_short_message,
      formatter_mediator=None):
    """Tests the formatting of message strings.

    This function invokes the GetMessages function of the event
    formatter on the event and compares the resulting messages
    strings with those expected.

    Args:
      event (EventObject): event.
      expected_message (str): expected message string.
      expected_short_message (str): expected short message  string.
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
    """
    if not formatter_mediator:
      formatter_mediator = mediator.FormatterMediator()
    message, message_short = formatter.GetMessages(formatter_mediator, event)
    self.assertEqual(message, expected_message)
    self.assertEqual(message_short, expected_short_message)
