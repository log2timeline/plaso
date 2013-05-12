#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains definition for a selective fields EventObjectFilter."""
from plaso.lib import errors
from plaso.lib import lexer
from plaso.filters import eventfilter


class SelectiveLexer(lexer.Lexer):
  """A simple selective filter lexer implementation."""

  tokens = [
    lexer.Token('INITIAL', r'SELECT', '', 'FIELDS'),
    lexer.Token('FIELDS', r'(.+) WHERE ', 'SetFields', 'FILTER'),
    lexer.Token('FIELDS', r'(.+) LIMIT', 'SetFields', 'LIMIT_END'),
    lexer.Token('FIELDS', r'(.+)$', 'SetFields', 'END'),
    lexer.Token('FILTER', r'(.+) LIMIT', 'SetFilter', 'LIMIT_END'),
    lexer.Token('FILTER', r'(.+)$', 'SetFilter', 'END'),
    lexer.Token('LIMIT_END', r'(.+)$', 'SetLimit', 'END')]

  def __init__(self, data=''):
    """Initialize the lexer."""
    self._fields = []
    self._limit = 0
    self._filter = None
    super(SelectiveLexer, self).__init__(data)

  __pychecker__ = 'unusednames=kwargs'
  def SetFilter(self, match, **kwargs):
    """Set the filter query."""
    self._filter = match.group(1)

  __pychecker__ = 'unusednames=kwargs'
  def SetLimit(self, match, **kwargs):
    """Set the row limit."""
    try:
      limit = int(match.group(1))
    except ValueError:
      self.Error('Invalid limit value, should be int [{}] = {}'.format(
          type(match.group(1)), match.group(1)))
      limit = 0

    self._limit = limit

  __pychecker__ = 'unusednames=kwargs'
  def SetFields(self, match, **kwargs):
    """Set the selective fields."""
    text = match.group(1).lower()
    field_text, _, _ = text.partition(' from ')

    use_field_text = field_text.replace(' ', '')
    if ',' in use_field_text:
      self._fields = use_field_text.split(',')
    else:
      self._fields = [use_field_text]


class DynamicFilter(eventfilter.EventObjectFilter):
  """A twist to the EventObjectFilter allowing output fields to be selected.

  This filter is essentially the same as the EventObjectFilter except it wraps
  it in a selection of which fields should be included by an output module that
  has support for selective fields. That is to say the filter:

    SELECT field_a, field_b WHERE attribute contains 'text'

  Will use the EventObjectFilter "attribute contains 'text'" and at the same
  time indicate to the appropriate output module that the user wants only the
  fields field_a and field_b to be used in the output.
  """

  @property
  def fields(self):
    """Set the fields property."""
    return self._fields

  @property
  def limit(self):
    """Return the limit of row counts."""
    return self._limit

  def __init__(self):
    """Initialize the selective EventObjectFilter."""
    super(DynamicFilter, self).__init__()
    self._fields = []
    self._limit = 0

  def CompileFilter(self, filter_string):
    """Compile the filter string into a EventObjectFilter matcher."""
    lex = SelectiveLexer(filter_string)

    _ = lex.NextToken()
    if lex.error:
      raise errors.WrongFilterPlugin('Malformed filter string.')

    _ = lex.NextToken()
    if lex.error:
      raise errors.WrongFilterPlugin('No fields defined.')

    if lex.state is not 'END':
      while lex.state is not 'END':
        _ = lex.NextToken()
        if lex.error:
          raise errors.WrongFilterPlugin('No filter defined for DynamicFilter.')

    if lex.state != 'END':
      raise errors.WrongFilterPlugin(
          'Malformed DynamicFilter, end state not reached.')

    self._fields = lex._fields
    self._limit = lex._limit

    if lex._filter:
      super(DynamicFilter, self).CompileFilter(lex._filter)
    else:
      self.matcher = None

