# -*- coding: utf-8 -*-
"""Event formatter related functions and classes for testing."""

from plaso.engine import knowledge_base
from plaso.output import mediator

from tests import test_lib as shared_test_lib


class EventFormatterTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an event formatter."""

  def _CreateOutputMediator(self, dynamic_time=True):
    """Creates a test output mediator.

    Args:
      dynamic_time (Optional[bool]): True if date and time values should be
          represented in their granularity or semantically.

    Returns:
      OutputMediator: output mediator.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()

    return mediator.OutputMediator(
        knowledge_base_object, data_location=shared_test_lib.TEST_DATA_PATH,
        dynamic_time=dynamic_time)

  def _TestGetFormatStringAttributeNames(
      self, event_formatter, expected_attribute_names):
    """Tests the GetFormatStringAttributeNames function.

    Args:
      event_formatter (EventFormatter): event formatter under test.
      expected_attribute_names (list[str]): expected attribute names.
    """
    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), sorted(expected_attribute_names))
