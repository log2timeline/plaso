# -*- coding: utf-8 -*-
"""Event formatter related functions and classes for testing."""

from plaso.output import mediator
from plaso.storage.fake import writer as fake_writer

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
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    return mediator.OutputMediator(
        storage_writer, data_location=shared_test_lib.TEST_DATA_PATH,
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
