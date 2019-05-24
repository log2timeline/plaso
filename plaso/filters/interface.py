# -*- coding: utf-8 -*-
"""Filter interface."""

from __future__ import unicode_literals

import abc


class FilterObject(object):
  """Filter object interface."""

  def __init__(self):
    """Initializes a filter object."""
    super(FilterObject, self).__init__()
    self._filter_expression = None
    self._matcher = None

  @property
  def fields(self):
    """list[str]: name of the fields."""
    return []

  @property
  def filter_expression(self):
    """object: compiled filter expression or None."""
    if self._filter_expression:
      return self._filter_expression

    return None

  @property
  def filter_name(self):
    """str: name of the filter."""
    return self.__class__.__name__

  @property
  def limit(self):
    """int: row limit."""
    return 0

  @property
  def separator(self):
    """str: output field separator."""
    return ','

  @abc.abstractmethod
  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    Args:
      filter_expression (str): filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """

  # pylint: disable=unused-argument
  def Match(self, event, event_data, event_tag):
    """Determines if an event matches the filter.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.

    Returns:
      bool: True if the event matches the filter.
    """
    return False
