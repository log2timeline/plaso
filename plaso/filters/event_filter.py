# -*- coding: utf-8 -*-
"""The event filter."""

from __future__ import unicode_literals

from plaso.filters import interface
from plaso.lib import pfilter


class EventObjectFilter(interface.FilterObject):
  """Event filter."""

  def __init__(self):
    """Initializes an event filter."""
    super(EventObjectFilter, self).__init__()
    self._decision = None
    self._event_filter = None
    self._filter_expression = None

  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    The filter expression contains an object filter expression.

    Args:
      filter_expression (str): filter expression.

    Raises:
      ParseError: if the filter expression cannot be parsed.
    """
    expression_parser = pfilter.EventFilterExpressionParser(filter_expression)
    expression = expression_parser.Parse()

    self._event_filter = expression.Compile(
        pfilter.PlasoAttributeFilterImplementation)
    self._filter_expression = filter_expression

  def Match(self, event):
    """Determines if an event matches the filter.

    Args:
      event (EventObject): an event.

    Returns:
      bool: True if the event matches the filter.
    """
    if not self._event_filter:
      return True

    self._decision = self._event_filter.Matches(event)
    return self._decision
