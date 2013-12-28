#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""The patterns classes used by the scan tree-based format scanner."""


class _ByteValuePatterns(object):
  """Class that implements a mapping between byte value and patterns.

     The byte value patterns are used in the scan tree-based format scanner
     to map a byte value to one or more patterns.
  """

  def __init__(self, byte_value):
    """Initializes the pattern table (entry) byte value.

    Args:
      byte_value: the byte value that maps the patterns in the table.
    """
    super(_ByteValuePatterns, self).__init__()
    self.byte_value = byte_value
    self.patterns = {}

  def __str__(self):
    """Retrieves a string representation of the byte value patterns."""
    return '0x{0:02x} {1!s}'.format(ord(self.byte_value), self.patterns)

  def AddPattern(self, pattern):
    """Adds a pattern.

    Args:
      pattern: the pattern (instance of Pattern).

    Raises:
      ValueError: if the table entry already contains a pattern
                  with the same identifier.
    """
    if pattern.identifier in self.patterns:
      raise ValueError(u'Pattern {0:s} is already defined.'.format(
          pattern.identifier))

    self.patterns[pattern.identifier] = pattern

  def ToDebugString(self, indentation_level=1):
    """Converts the byte value pattern into a debug string."""
    indentation = u'  ' * indentation_level

    header = u'{0:s}byte value: 0x{1:02x}\n'.format(
        indentation, ord(self.byte_value))

    entries = u''.join([u'{0:s}  patterns: {1:s}\n'.format(
        indentation, identifier) for identifier in self.patterns])

    return u''.join([header, entries, u'\n'])


class _SkipTable(object):
  """Class that implements a skip table.

     The skip table is used in the scan tree-based format scanner to determine
     the skip value for the Boyer–Moore–Horspool search.
  """

  def __init__(self, skip_pattern_length):
    """Initializes the skip table.

    Args:
      skip_pattern_length: the (maximum) skip pattern length.
    """
    super(_SkipTable, self).__init__()
    self._skip_value_per_byte_value = {}
    self.skip_pattern_length = skip_pattern_length

  def __getitem__(self, key):
    """Retrieves a specific skip value.

    Args:
      key: the byte value within the skip table.

    Returns:
      the skip value for the key or the maximim skip value
      if no corresponding key was found.
    """
    if key in self._skip_value_per_byte_value:
      return self._skip_value_per_byte_value[key]
    return self.skip_pattern_length

  def SetSkipValue(self, byte_value, skip_value):
    """Sets a skip value.

    Args:
      byte_value: the corresponding byte value.
      skip_value: the number of bytes to skip.

    Raises:
      ValueError: if byte value or skip value is out of bounds.
    """
    if byte_value < 0 or byte_value > 255:
      raise ValueError(u'Invalid byte value, value out of bounds.')

    if skip_value < 0 or skip_value >= self.skip_pattern_length:
      raise ValueError(u'Invalid skip value, value out of bounds.')

    if (not byte_value in self._skip_value_per_byte_value or
        self._skip_value_per_byte_value[byte_value] > skip_value):
      self._skip_value_per_byte_value[byte_value] = skip_value

  def ToDebugString(self):
    """Converts the skip table into a debug string."""
    header = u'Byte value\tSkip value\n'

    entries = u''.join([u'0x{0:02x}\t{1:d}\n'.format(
        byte_value, self._skip_value_per_byte_value[byte_value])
                        for byte_value in self._skip_value_per_byte_value])

    default = u'Default\t{0:d}\n'.format(self.skip_pattern_length)

    return u''.join([header, entries, default, u'\n'])


class Pattern(object):
  """Class that implements a pattern."""

  def __init__(self, signature_index, signature, specification):
    """Initializes the pattern.

    Args:
      signature_index: the index of the signature within the specification.
      signature: the signature (instance of Signature).
      specification: the specification (instance of Specification) that
                     contains the signature.
    """
    super(Pattern, self).__init__()
    self._signature_index = signature_index
    self.signature = signature
    self.specification = specification

  def __str__(self):
    """Retrieves a string representation."""
    return self.identifier

  @property
  def expression(self):
    """The signature expression."""
    return self.signature.expression

  @property
  def identifier(self):
    """The identifier."""
    # Using _ here because some scanner implementation are limited to what
    # characters can be used in the identifiers.
    return u'{0:s}_{1:d}'.format(
        self.specification.identifier, self._signature_index)

  @property
  def offset(self):
    """The signature offset."""
    return self.signature.offset

  @property
  def is_bound(self):
    """Boolean value to indicate the signature is bound to an offset."""
    return self.signature.is_bound


class PatternTable(object):
  """Class that implements a pattern table.

     The pattern table is used in the the scan tree-based format scanner
     to construct a scan tree. It contains either unbound patterns or
     patterns bound to a specific offset.
  """

  def __init__(self, patterns, ignore_list, is_bound=None):
    """Initializes and builds the patterns table from patterns.

    Args:
      patterns: a list of the patterns.
      ignore_list: a list of pattern offsets to ignore.
      is_bound: optional boolean value to indicate if the signatures are bound
                to offsets. The default is None, which means the value should
                be ignored and both bound and unbound patterns are considered
                unbound.

    Raises:
      ValueError: if a signature pattern is too small to be useful (< 4).
    """
    super(PatternTable, self).__init__()
    self._byte_values_per_offset = {}
    self.patterns = []
    self.largest_pattern_length = 0
    self.smallest_pattern_length = 0

    for pattern in patterns:
      if is_bound is not None and pattern.signature.is_bound != is_bound:
        continue

      pattern_length = len(pattern.expression)

      if pattern_length < 4:
        raise ValueError(u'Pattern too small to be useful.')

      self.smallest_pattern_length = min(
          self.smallest_pattern_length, pattern_length)

      self.largest_pattern_length = max(
          self.largest_pattern_length, pattern_length)

      self.patterns.append(pattern)

      self._AddPattern(pattern, ignore_list, is_bound)

  def _AddPattern(self, pattern, ignore_list, is_bound):
    """Addes the byte values per offset in the pattern to the table.

    Args:
      pattern: the pattern (instance of Pattern).
      ignore_list: a list of pattern offsets to ignore.
      is_bound: boolean value to indicate if the signatures are bound
                to offsets. A value of None indicates that the value should
                be ignored and both bound and unbound patterns are considered
                unbound.
    """
    pattern_offset = pattern.offset if is_bound else 0

    for byte_value in pattern.expression:
      if not pattern_offset in self._byte_values_per_offset:
        self._byte_values_per_offset[pattern_offset] = {}

      if not pattern_offset in ignore_list:
        byte_values = self._byte_values_per_offset[pattern_offset]

        if not byte_value in byte_values:
          byte_values[byte_value] = _ByteValuePatterns(byte_value)

        byte_value_patterns = byte_values[byte_value]

        byte_value_patterns.AddPattern(pattern)

      pattern_offset += 1

  @property
  def offsets(self):
    """The offsets."""
    return self._byte_values_per_offset.keys()

  def GetByteValues(self, pattern_offset):
    """Returns the bytes values for a specific pattern offset."""
    return self._byte_values_per_offset[pattern_offset]

  def GetSkipTable(self):
    """Retrieves the skip table for the patterns in the table.

    Returns:
      The skip table (instance of SkipTable).
    """
    skip_table = _SkipTable(self.smallest_pattern_length)

    for pattern in self.patterns:
      if pattern.expression:
        skip_value = self.smallest_pattern_length

        for expression_index in range(0, self.smallest_pattern_length):
          skip_value -= 1
          skip_table.SetSkipValue(
              ord(pattern.expression[expression_index]), skip_value)

    return skip_table

  def ToDebugString(self):
    """Converts the pattern table into a debug string."""
    header = u'Pattern offset\tByte value(s)\n'
    entries = u''

    for pattern_offset in self._byte_values_per_offset:
      entries += u'{0:d}'.format(pattern_offset)

      byte_values = self._byte_values_per_offset[pattern_offset]

      for byte_value in byte_values:
        identifiers = u', '.join(
            [identifier for identifier in byte_values[byte_value].patterns])

        entries += u'\t0x{0:02x} ({1:s})'.format(ord(byte_value), identifiers)

      entries += u'\n'

    return u''.join([header, entries, u'\n'])
