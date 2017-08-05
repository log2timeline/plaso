# -*- coding: utf-8 -*-
"""Filter interface."""

from __future__ import unicode_literals

import abc

from plaso.lib import errors
from plaso.lib import pfilter


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
    """The output field separator value."""
    return ','

  def _GetMatcher(self, filter_expression):
    """Retrieves a filter object for a specific filter expression.

    Args:
      filter_expression: string that contains the filter expression.

    Returns:
      object: filter or None.
    """
    try:
      parser = pfilter.BaseParser(filter_expression).Parse()
      return parser.Compile(pfilter.PlasoAttributeFilterImplementation)

    except errors.ParseError:
      pass

  @abc.abstractmethod
  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    Args:
      filter_expression (str): filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """

  def Match(self, unused_event):
    """Determines if an event matches the filter.

    Args:
      event (EventObject): event.

    Returns:
      bool: True if the there is a match.
    """
    return False
