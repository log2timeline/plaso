#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A definition of the filter interface for filters in plaso."""

import abc

from plaso.lib import errors
from plaso.lib import registry


class FilterObject(object):
  """The interface that each filter needs to implement in plaso."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

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

  @abc.abstractmethod
  def CompileFilter(self, filter_string):   # pylint: disable-msg=W0613
    """Verify filter string and prepare the filter for later usage.

    This function verifies the filter string matches the definition of
    the class and if necessary compiles or prepares the filter so it can start
    matching against passed in EventObjects.

    Args:
      filter_string: A string passed in that should be recognized by the filter
                     class.

    Raises:
      errors.WrongPlugin: If this filter string does not match the filter
                          class.
    """
    raise errors.WrongPlugin('Not the correct filter for this string.')

  def Match(self, event_object):    # pylint: disable-msg=W0613
    """Compare an EventObject to the filter expression and return a boolean.

    This function returns True if the filter should be passed through the filter
    and False otherwise.

    Args:
      event_object: An EventObject that should be evaluated against the filter.

    Returns:
      Boolean indicating whether the filter matches the object or not.
    """
    return False

