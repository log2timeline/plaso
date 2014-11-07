#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains definition for a simple filter."""
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

