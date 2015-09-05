# -*- coding: utf-8 -*-
import unittest

from plaso.filters import interface


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


class FilterTestCase(unittest.TestCase):
  """The unit test case for an event filter."""
