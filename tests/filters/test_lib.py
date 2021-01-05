# -*- coding: utf-8 -*-
"""The filters shared test library."""

from plaso.filters import event_filter

from tests import test_lib as shared_test_lib


class TestEventFilter(event_filter.EventObjectFilter):
  """Test event filter."""

  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    Args:
      filter_expression (str): filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """
    return


class FilterTestCase(shared_test_lib.BaseTestCase):
  """Event filter test case."""
