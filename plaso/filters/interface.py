# -*- coding: utf-8 -*-
"""A definition of the filter interface for filters in plaso."""

import abc

from plaso.lib import errors
from plaso.lib import registry


class FilterObject(object):
  """The interface that each filter needs to implement in plaso."""

  # TODO: Re-factor into filters/interface and use a manager instead
  # of the registry library.
  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

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
    return getattr(self, '_decision', None)

  @property
  def last_reason(self):
    """Return the last reason for the match, if there was one."""
    if getattr(self, 'last_decision', False):
      return getattr(self, '_reason', '')

  @property
  def fields(self):
    """Return a list of fields for adaptive output modules."""
    return []

  @property
  def separator(self):
    """Return a separator for adaptive output modules."""
    return ','

  @property
  def limit(self):
    """Returns the max number of records to return, or zero for all records."""
    return 0

  def __init__(self):
    """Initialize the filter object."""
    super(FilterObject, self).__init__()
    self._filter_expression = None
    self._matcher = None

  @abc.abstractmethod
  def CompileFilter(self, unused_filter_string):
    """Verify filter string and prepare the filter for later usage.

    This function verifies the filter string matches the definition of
    the class and if necessary compiles or prepares the filter so it can start
    matching against passed in EventObjects.

    Args:
      unused_filter_string: A string passed in that should be recognized by
                            the filter class.

    Raises:
      errors.WrongPlugin: If this filter string does not match the filter
                          class.
    """
    raise errors.WrongPlugin('Not the correct filter for this string.')

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
