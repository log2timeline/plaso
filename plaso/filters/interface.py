# -*- coding: utf-8 -*-
"""The filter interface classes."""

import abc

from plaso.lib import objectfilter
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
    """Return the last matching decision."""
    return getattr(self, u'_decision', None)

  @property
  def last_reason(self):
    """Return the last reason for the match, if there was one."""
    if getattr(self, u'last_decision', False):
      return getattr(self, u'_reason', u'')

  @property
  def limit(self):
    """Returns the max number of records to return, or zero for all records."""
    return 0

  @property
  def separator(self):
    """Return a separator for adaptive output modules."""
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

    except objectfilter.ParseError:
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
    """Compare an EventObject to the filter expression and return a boolean.

    This function returns True if the filter should be passed through the filter
    and False otherwise.

    Args:
      unused_event_object: An event object (instance of EventObject) that
                           should be evaluated against the filter.

    Returns:
      Boolean indicating whether the filter matches the object or not.
    """
    return False
