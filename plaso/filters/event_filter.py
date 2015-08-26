# -*- coding: utf-8 -*-

from plaso.filters import interface
from plaso.filters import manager
from plaso.lib import errors
from plaso.lib import pfilter


class EventObjectFilter(interface.FilterObject):
  """Class that implements an event object filter."""

  def CompileFilter(self, filter_string):
    """Compile the filter string into a filter matcher.

    Args:
      filter_string: TODO

    Raises:
      WrongPlugin: TODO
    """
    self._matcher = pfilter.GetMatcher(filter_string, True)
    if not self._matcher:
      raise errors.WrongPlugin('Malformed filter string.')
    self._filter_expression = filter_string

  def Match(self, event_object):
    """Determines if the filter matches an event object.

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
