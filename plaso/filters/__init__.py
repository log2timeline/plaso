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
"""This file contains an import statement for each filter."""
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
  """Evaluate filters against a filter string and return the first match."""
  for filter_obj in ListFilters():
    try:
      filter_obj.CompileFilter(filter_string)
      return filter_obj
    except errors.WrongPlugin:
      logging.debug(u'Filterstring [{}] is not a filter: {}'.format(
          filter_string, filter_obj.filter_name))
