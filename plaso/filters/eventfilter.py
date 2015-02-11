# -*- coding: utf-8 -*-
from plaso.lib import errors
from plaso.lib import filter_interface
from plaso.lib import pfilter


class EventObjectFilter(filter_interface.FilterObject):
  """A simple filter using the objectfilter library."""

  def CompileFilter(self, filter_string):
    """Compile the filter string into a filter matcher."""
    self.matcher = pfilter.GetMatcher(filter_string, True)
    if not self.matcher:
      raise errors.WrongPlugin('Malformed filter string.')

  def Match(self, event_object):
    """Evaluate an EventObject against a filter."""
    if not self.matcher:
      return True

    self._decision = self.matcher.Matches(event_object)

    return self._decision

