# -*- coding: utf-8 -*-
"""The event filter."""

from __future__ import unicode_literals

import copy

from plaso.filters import expression_parser
from plaso.filters import interface


class EventObjectFilter(interface.FilterObject):
  """Event filter."""

  def __init__(self):
    """Initializes an event filter."""
    super(EventObjectFilter, self).__init__()
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
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(filter_expression)

    self._event_filter = expression.Compile()
    self._filter_expression = filter_expression

  def Match(self, event, event_data, event_tag):
    """Determines if an event matches the filter.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.

    Returns:
      bool: True if the event matches the filter.
    """
    if not self._event_filter:
      return True

    # TODO: refactor to separately filter event, event data and event tag.
    copy_of_event = copy.deepcopy(event)
    for attribute_name, attribute_value in event_data.GetAttributes():
      setattr(copy_of_event, attribute_name, attribute_value)

    copy_of_event.tag = event_tag
    # TODO: end refactor

    return self._event_filter.Matches(copy_of_event)
