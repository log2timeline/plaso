# -*- coding: utf-8 -*-
from plaso.lib import errors
from plaso.lib import filter_interface
from plaso.lib import pfilter


class EventObjectFilter(filter_interface.FilterObject):
  """A simple filter using the objectfilter library."""

  def CompileFilter(self, filter_string):
    """Compile the filter string into a filter matcher."""
    self._matcher = pfilter.GetMatcher(filter_string, True)
    if not self._matcher:
      raise errors.WrongPlugin('Malformed filter string.')
    self._filter_expression = filter_string

  def Match(self, event_object):
    """Evaluate an EventObject against a filter."""
    if not self._matcher:
      return True

    self._decision = self._matcher.Matches(event_object)

    return self._decision

