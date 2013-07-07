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
    lexer.Token('FIELDS', r'(.+) SEPARATED BY', 'SetFields', 'SEPARATE'),
    lexer.Token('FIELDS', r'(.+)$', 'SetFields', 'END'),
    lexer.Token('FILTER', r'(.+) SEPARATED BY', 'SetFilter', 'SEPARATE'),
    lexer.Token('FILTER', r'(.+) LIMIT', 'SetFilter', 'LIMIT_END'),
    lexer.Token('FILTER', r'(.+)$', 'SetFilter', 'END'),
    lexer.Token('SEPARATE', r' ', '', ''),  # Ignore white space here.
    lexer.Token('SEPARATE', r'LIMIT', '', 'LIMIT_END'),
    lexer.Token(
        'SEPARATE', r'[\'"]([^ \'"]+)[\'"] LIMIT', 'SetSeparator',
        'LIMIT_END'),
    lexer.Token(
        'SEPARATE', r'[\'"]([^ \'"]+)[\'"]$', 'SetSeparator', 'END'),
    lexer.Token(
        'SEPARATE', r'(.+)$', 'SetSeparator', 'END'),
    lexer.Token(
        'LIMIT_END', r'SEPARATED BY [\'"]([^\'"]+)[\'"]', 'SetSeparator', ''),
    lexer.Token('LIMIT_END', r'(.+) SEPARATED BY', 'SetLimit', 'SEPARATE'),
    lexer.Token('LIMIT_END', r'(.+)$', 'SetLimit', 'END')]

  def __init__(self, data=''):
    """Initialize the lexer."""
    self.fields = []
    self.limit = 0
    self.lex_filter = None
    self.separator = u','
    super(SelectiveLexer, self).__init__(data)

  def SetFilter(self, match, **_):
    """Set the filter query."""
    filter_match = match.group(1)
    if 'LIMIT' in filter_match:
      # This only occurs in the case where we have "LIMIT X SEPARATED BY".
      self.lex_filter, _, push_back = filter_match.rpartition('LIMIT')
      self.PushBack('LIMIT {} SEPARATED BY '.format(push_back))
    else:
      self.lex_filter = filter_match

  def SetSeparator(self, match, **_):
    """Set the separator of the output, only uses the first char."""
    separator = match.group(1)
    if separator:
      self.separator = separator[0]

  def SetLimit(self, match, **_):
    """Set the row limit."""
    try:
      limit = int(match.group(1))
    except ValueError:
      self.Error('Invalid limit value, should be int [{}] = {}'.format(
          type(match.group(1)), match.group(1)))
      limit = 0

    self.limit = limit

  def SetFields(self, match, **_):
    """Set the selective fields."""
    text = match.group(1).lower()
    field_text, _, _ = text.partition(' from ')

    use_field_text = field_text.replace(' ', '')
    if ',' in use_field_text:
      self.fields = use_field_text.split(',')
    else:
      self.fields = [use_field_text]


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

  @property
  def separator(self):
    """Return the separator value."""
    return self._separator

  def __init__(self):
    """Initialize the selective EventObjectFilter."""
    super(DynamicFilter, self).__init__()
    self._fields = []
    self._limit = 0
    self._separator = u','

  def CompileFilter(self, filter_string):
    """Compile the filter string into a EventObjectFilter matcher."""
    lex = SelectiveLexer(filter_string)

    _ = lex.NextToken()
    if lex.error:
      raise errors.WrongPlugin('Malformed filter string.')

    _ = lex.NextToken()
    if lex.error:
      raise errors.WrongPlugin('No fields defined.')

    if lex.state is not 'END':
      while lex.state is not 'END':
        _ = lex.NextToken()
        if lex.error:
          raise errors.WrongPlugin('No filter defined for DynamicFilter.')

    if lex.state != 'END':
      raise errors.WrongPlugin(
          'Malformed DynamicFilter, end state not reached.')

    self._fields = lex.fields
    self._limit = lex.limit
    self._separator = unicode(lex.separator)

    if lex.lex_filter:
      super(DynamicFilter, self).CompileFilter(lex.lex_filter)
    else:
      self.matcher = None

