# -*- coding: utf-8 -*-
"""The filter interface classes."""

import abc

from plaso.lib import errors
from plaso.lib import pfilter


class FilterObject(object):
  """The filter interface class."""

  def __init__(self):
    """Initialize the filter object."""
    super(FilterObject, self).__init__()
    self._filter_expression = None
    self._matcher = None

  @property
  def fields(self):
    """Return a list of fields for adaptive output modules."""
    return []

  @property
  def filter_expression(self):
    """Return the compiled filter expression or None if not compiled."""
    if self._filter_expression:
      return self._filter_expression

  @property
  def filter_name(self):
    """Return the name of the filter."""
    return self.__class__.__name__

  @property
  def last_decision(self):
    """The last matching decision or None."""
    return getattr(self, u'_decision', None)

  @property
  def last_reason(self):
    """The last reason for the match or None."""
    if getattr(self, u'_decision', False):
      return getattr(self, u'_reason', u'')

  @property
  def limit(self):
    """The row limit."""
    return 0

  @property
  def separator(self):
    """The output field separator value."""
    return u','

  def _GetMatcher(self, filter_expression):
    """Retrieves a filter object for a specific filter expression.

    Args:
      filter_expression: string that contains the filter expression.

    Returns:
      A filter object (instance of objectfilter.TODO) or None.
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
      filter_expression: string that contains the filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """

  def Match(self, unused_event_object):
    """Determines if an event object matches the filter.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A boolean value that indicates a match.
    """
    return False
