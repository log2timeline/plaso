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
"""This file contains utility functions."""

from plaso.lib import errors
from plaso.lib import lexer

RESERVED_VARIABLES = frozenset(
    ['username', 'inode', 'hostname', 'body', 'parser', 'regvalue', 'timestamp',
     'timestamp_desc', 'source_short', 'source_long', 'timezone', 'filename',
     'display_name', 'pathspec', 'offset', 'store_number', 'store_index',
     'tag', 'data_type', 'metadata', 'http_headers', 'query'])


def GetUnicodeString(string):
  """Converts the string to Unicode if necessary."""
  if type(string) != unicode:
    return str(string).decode('utf8', 'ignore')
  return string


class PathReplacer(lexer.Lexer):
  """Replace path variables with values gathered from earlier preprocessing."""

  tokens = [
      lexer.Token('.', '{{([^}]+)}}', 'ReplaceVariable', ''),
      lexer.Token('.', '{([^}]+)}', 'ReplaceString', ''),
      lexer.Token('.', '([^{])', 'ParseString', ''),
      ]

  def __init__(self, pre_obj, data=''):
    """Constructor for a path replacer."""
    super(PathReplacer, self).__init__(data)
    self._path = []
    self._pre_obj = pre_obj

  def GetPath(self):
    """Run the lexer and replace path."""
    while 1:
      _ = self.NextToken()
      if self.Empty():
        break

    return u''.join(self._path)

  def ParseString(self, match, **_):
    """Append a string to the path."""
    self._path.append(match.group(1))

  def ReplaceVariable(self, match, **_):
    """Replace a string that should not be a variable."""
    self._path.append(u'{%s}' % match.group(1))

  def ReplaceString(self, match, **_):
    """Replace a variable with a given attribute."""
    replace = getattr(self._pre_obj, match.group(1), None)

    if replace:
      self._path.append(replace)
    else:
      raise errors.PathNotFound(
          u'Path variable: {} not discovered yet.'.format(match.group(1)))


def FormatHeader(header):
  """Format and return a header for output."""
  return '\n{:*^80}'.format(u' %s ' % header)


def FormatOutputString(name, description, col_length=25):
  """Return a formatted string ready for output."""
  max_width = 80
  line_length = max_width - col_length - 3

  fmt = u'{:>%ds} : {}' % col_length
  fmt_second = u'{:<%d}{}' % (col_length + 3)

  description = unicode(description)
  if len(description) < line_length:
    return fmt.format(name, description)

  # Split each word up in the description.
  words = description.split()

  current = 0
  line_count = len(description) / line_length + 1
  word_count = len(words) / line_count + 1

  lines = []
  word_buffer = []
  for word in words:
    current += len(word) + 1
    if current >= line_length:
      current = len(word)
      lines.append(u' '.join(word_buffer))
      word_buffer = [word]
    else:
      word_buffer.append(word)
  lines.append(u' '.join(word_buffer))

  ret = []
  ret.append(fmt.format(name, lines[0]))
  for line in lines[1:]:
    ret.append(fmt_second.format('', line))

  return u'\n'.join(ret)

