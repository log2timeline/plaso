# -*- coding: utf-8 -*-
"""Event formatter related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.formatters import interface

from tests import test_lib as shared_test_lib


class TestEventFormatter(interface.EventFormatter):
  """Test event formatter."""

  DATA_TYPE = 'test:event'
  FORMAT_STRING = '{text}'

  SOURCE_SHORT = 'FILE'
  SOURCE_LONG = 'Weird Log File'


class EventFormatterTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an event formatter."""

  def _TestGetFormatStringAttributeNames(
      self, event_formatter, expected_attribute_names):
    """Tests the GetFormatStringAttributeNames function.

    Args:
      event_formatter (EventFormatter): event formatter under test.
      expected_attribute_names (list[str]): expected attribute names.
    """
    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), sorted(expected_attribute_names))
