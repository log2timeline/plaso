# -*- coding: utf-8 -*-
"""The event object filter."""

from plaso.filters import interface
from plaso.filters import manager
from plaso.lib import errors


class EventObjectFilter(interface.FilterObject):
  """Class that implements an event object filter."""

  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    The filter expression contains an object filter expression.

    Args:
      filter_expression: string that contains the filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """
    matcher = self._GetMatcher(filter_expression)
    if not matcher:
      raise errors.WrongPlugin(u'Malformed filter expression.')

    self._filter_expression = filter_expression
    self._matcher = matcher

  def Match(self, event_object):
    """Determines if an event object matches the filter.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A boolean value that indicates a match.
    """
    if not self._matcher:
      return True

    self._decision = self._matcher.Matches(event_object)
    return self._decision


manager.FiltersManager.RegisterFilter(EventObjectFilter)
