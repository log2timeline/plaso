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
"""This file contains definition for a list of ObjectFilter."""
import os
import yaml
import logging

from plaso.lib import errors
from plaso.lib import filter_interface
from plaso.lib import pfilter


def IncludeKeyword(loader, node):
  """A constructor for the include keyword in YAML."""
  filename = loader.construct_scalar(node)
  if os.path.isfile(filename):
    with open(filename, 'rb') as fh:
      try:
        data = yaml.safe_load(fh)
      except yaml.ParserError as e:
        logging.error(u'Unable to load rule file: {}'.format(e))
        return None
  return data


class ObjectFilterList(filter_interface.FilterObject):
  """A series of Pfilter filters along with metadata."""

  def CompileFilter(self, filter_string):
    """Compile a set of ObjectFilters defined in an YAML file."""
    if not os.path.isfile(filter_string):
      raise errors.WrongFilterPlugin((
          'ObjectFilterList requires an YAML file to be passed on, this filter '
          'string is not a file.'))

    yaml.add_constructor('!include', IncludeKeyword,
                         Loader=yaml.loader.SafeLoader)
    results = None

    with open(filter_string, 'rb') as fh:
      try:
        results = yaml.safe_load(fh)
      except (yaml.ScannerError, IOError) as e:
        raise errors.WrongFilterPlugin(
            u'Malformed YAML file: {}.'.format(e))

    self.filters = []
    if type(results) is dict:
      self._ParseEntry(results)
    elif type(results) is list:
      for result in results:
        if type(result) is not dict:
          raise errors.WrongFilterPlugin(
              u'Wrong format of YAML file, entry not a dict ({})'.format(
                  type(result)))
        self._ParseEntry(result)
    else:
      raise errors.WrongFilterPlugin(
          u'Wrong format of YAML file, entry not a dict ({})'.format(
              type(result)))

  def _ParseEntry(self, entry):
    """Parse a single YAML filter entry."""
    # A single file with a list of filters to parse.
    for name, meta in entry.items():
      if 'filter' not in meta:
        raise errors.WrongFilterPlugin(
            u'Entry inside {} does not contain a filter statement.'.format(
                name))

      matcher = pfilter.GetMatcher(meta.get('filter'), True)
      if not matcher:
        raise errors.WrongFilterPlugin(
          u'Filter entry [{}] malformed for rule: <{}>'.format(
            meta.get('filter'), name))

      self.filters.append((name, matcher, meta))

  def Match(self, event_object):
    """Evaluate an EventObject against a pfilter."""
    if not self.filters:
      return True

    for name, matcher, meta in self.filters:
      self._decision = matcher.Matches(event_object)
      if self._decision:
        self._reason = u'[{}] {} {}'.format(
            name, meta.get('description', 'N/A'), u' - '.join(
                meta.get('urls', [])))
        return True

    return False


