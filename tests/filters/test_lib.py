# -*- coding: utf-8 -*-
"""The filters shared test library."""

from __future__ import unicode_literals

from plaso.filters import interface

from tests import test_lib as shared_test_lib


class TestEventFilter(interface.FilterObject):
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
  """The unit test case for an event filter."""
