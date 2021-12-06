# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

from plaso.engine import knowledge_base
from plaso.output import mediator

from tests import test_lib as shared_test_lib


class OutputModuleTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a output module."""

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
