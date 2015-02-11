# -*- coding: utf-8 -*-
import logging

from plaso.filters import dynamic_filter
from plaso.filters import eventfilter
from plaso.filters import filterlist

from plaso.lib import filter_interface
from plaso.lib import errors


def ListFilters():
  """Generate a list of all available filters."""
  filters = []
  for cl in filter_interface.FilterObject.classes:
    filters.append(filter_interface.FilterObject.classes[cl]())

  return filters


def GetFilter(filter_string):
  """Returns the first filter that matches the filter string.

  Args:
    filter_string: A filter string for any of the available filters.

  Returns:
   The first FilterObject found matching the filter string. If no FilterObject
   is available for this filter string None is returned.
  """
  if not filter_string:
    return

  for filter_obj in ListFilters():
    try:
      filter_obj.CompileFilter(filter_string)
      return filter_obj
    except errors.WrongPlugin:
      logging.debug(u'Filterstring [{}] is not a filter: {}'.format(
          filter_string, filter_obj.filter_name))
