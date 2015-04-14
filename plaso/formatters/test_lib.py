# -*- coding: utf-8 -*-
"""Event formatter related functions and classes for testing."""

import unittest

from plaso.formatters import interface


class TestEventFormatter(interface.EventFormatter):
  """Class to define a formatter for a test event."""
  DATA_TYPE = 'test:event'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = 'FILE'
  SOURCE_LONG = 'Weird Log File'


class EventFormatterTestCase(unittest.TestCase):
  """The unit test case for an event formatter."""

  def _TestGetFormatStringAttributeNames(
      self, event_formatter, expected_attribute_names):
    """Tests the GetFormatStringAttributeNames function.

    Args:
      event_formatter: the event formatter (instance of EventFormatter).
      expected_attribute_names: list of the expected attribute names.
    """
    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), sorted(expected_attribute_names))
