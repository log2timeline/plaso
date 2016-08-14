# -*- coding: utf-8 -*-
"""The filters shared test library."""

from plaso.filters import interface

from tests import test_lib as shared_test_lib


class TestEventFilter(interface.FilterObject):
  """Class to define a filter for a test event."""

  def CompileFilter(self, unused_filter_expression):
    """Compiles the filter expression.

    Args:
      filter_expression: string that contains the filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """
    pass


class FilterTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an event filter."""
