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
"""The scan tree classes used by the scan tree-based format scanner."""

import logging

from plaso.classifier import patterns
from plaso.classifier import range_list


class _PatternWeights(object):
  """Class that implements pattern weights."""

  def __init__(self):
    """Initializes the pattern weights."""
    super(_PatternWeights, self).__init__()
    self._offsets_per_weight = {}
    self._weight_per_offset = {}

  def AddOffset(self, pattern_offset):
    """Adds a pattern offset and sets its weight to 0.

    Args:
      pattern_offset: the pattern offset to add to the pattern weights.

    Raises:
      ValueError: if the pattern weights already contains the pattern offset.
    """
    if pattern_offset in self._weight_per_offset:
      raise ValueError(u'Pattern offset already set.')

    self._weight_per_offset[pattern_offset] = 0

  def AddWeight(self, pattern_offset, weight):
    """Adds a weight for a specific pattern offset.

    Args:
      pattern_offset: the pattern offset to add to the pattern weights.
      weight: the corresponding weight to add.

    Raises:
      ValueError: if the pattern weights does not contain the pattern offset.
    """
    if not pattern_offset in self._weight_per_offset:
      raise ValueError(u'Pattern offset not set.')

    self._weight_per_offset[pattern_offset] += weight

    if not weight in self._offsets_per_weight:
      self._offsets_per_weight[weight] = []

    self._offsets_per_weight[weight].append(pattern_offset)

  def GetLargestWeight(self):
    """Retrieves the largest weight or 0 if none."""
    if self._offsets_per_weight:
      return max(self._offsets_per_weight)

    return 0

  def GetOffsetsForWeight(self, weight):
    """Retrieves the list of offsets for a specific weight."""
    return self._offsets_per_weight[weight]

  def GetWeightForOffset(self, pattern_offset):
    """Retrieves the weight for a specific pattern offset."""
    return self._weight_per_offset[pattern_offset]

  def ToDebugString(self):
    """Converts the pattern weights into a debug string."""
    header1 = u'Pattern offset\tWeight\n'

    entries1 = u''.join([u'{0:d}\t{1:d}\n'.format(
        pattern_offset, self._weight_per_offset[pattern_offset])
                         for pattern_offset in self._weight_per_offset])

    header2 = u'Weight\tPattern offset(s)\n'

    entries2 = u''.join([u'{0:d}\t{1!s}\n'.format(
        weight, self._offsets_per_weight[weight])
                         for weight in self._offsets_per_weight])

    return u''.join([header1, entries1, u'\n', header2, entries2, u'\n'])

  def SetWeight(self, pattern_offset, weight):
    """Sets a weight for a specific pattern offset.

    Args:
      pattern_offset: the pattern offset to set in the pattern weights.
      weight: the corresponding weight to set.

    Raises:
      ValueError: if the pattern weights does not contain the pattern offset.
    """
    if not pattern_offset in self._weight_per_offset:
      raise ValueError(u'Pattern offset not set.')

    self._weight_per_offset[pattern_offset] = weight

    if not weight in self._offsets_per_weight:
      self._offsets_per_weight[weight] = []

    self._offsets_per_weight[weight].append(pattern_offset)


class ScanTree(object):
  """Class that implements a scan tree."""

  _COMMON_BYTE_VALUES = frozenset(
      '\x00\x01\xff\t\n\r 0123456789'
      'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      'abcdefghijklmnopqrstuvwxyz')

  # The offset must be positive, negative offsets are ignored.
  OFFSET_MODE_POSITIVE = 1
  # The offset must be negative, positive offsets are ignored.
  OFFSET_MODE_NEGATIVE = 2
  # The offset must be positive, an error is raised for negative offsets.
  OFFSET_MODE_POSITIVE_STRICT = 3
  # The offset must be negative, an error is raised for positive offsets.
  OFFSET_MODE_NEGATIVE_STRICT = 4

  def __init__(
      self, specification_store, is_bound,
      offset_mode=OFFSET_MODE_POSITIVE_STRICT):
    """Initializes and builds the scan tree.

    Args:
      specification_store: the specification store (instance of
                           SpecificationStore) that contains the format
                           specifications.
      is_bound: boolean value to indicate if the signatures are bound
                to offsets. A value of None indicates that the value should
                be ignored and both bound and unbound patterns are considered
                unbound.
      offset_mode: optional value to indicate how the signature offsets should
                   be handled. The default is that the offset must be positive
                   and an error is raised for negative offsets.
    """
    super(ScanTree, self).__init__()
    self.pattern_list = []
    self.range_list = range_list.RangeList()

    # First determine all the patterns from the specification store.
    self._BuildPatterns(specification_store, is_bound, offset_mode=offset_mode)

    # Next create the scan tree starting with the root node.
    ignore_list = []
    pattern_table = patterns.PatternTable(
        self.pattern_list, ignore_list, is_bound)

    if pattern_table.patterns:
      self.root_node = self._BuildScanTreeNode(
          pattern_table, ignore_list, is_bound)

      logging.debug(
          u'Scan tree:\n%s', self.root_node.ToDebugString())

    # At the end the skip table is determined to provide for the
    # Boyer–Moore–Horspool skip value.
    self.skip_table = pattern_table.GetSkipTable()

    logging.debug(
        u'Skip table:\n%s', self.skip_table.ToDebugString())

    self.largest_length = pattern_table.largest_pattern_length

  def _BuildPatterns(
      self, specification_store, is_bound,
      offset_mode=OFFSET_MODE_POSITIVE_STRICT):
    """Builds the list of patterns.

    Args:
      specification_store: the specification store (instance of
                           SpecificationStore) that contains the format
                           specifications.
      is_bound: boolean value to indicate if the signatures are bound
                to offsets. A value of None indicates that the value should
                be ignored and both bound and unbound patterns are considered
                unbound.
      offset_mode: optional value to indicate how the signature offsets should
                   be handled. The default is that the offset must be positive
                   and an error is raised for negative offsets.

    Raises:
      ValueError: if a signature offset invalid according to specified offset
                  mode or a signature pattern is too small to be useful (< 4).
    """
    self.pattern_list = []

    for specification in specification_store.specifications:
      signature_index = 0

      for signature in specification.signatures:
        if signature.expression:
          signature_offset = signature.offset if is_bound else 0
          signature_pattern_length = len(signature.expression)

          if signature_offset < 0:
            if offset_mode == self.OFFSET_MODE_POSITIVE:
              continue
            elif offset_mode == self.OFFSET_MODE_POSITIVE_STRICT:
              raise ValueError(u'Signature offset less than 0.')

            # The range list does not allow offsets to be negative.
            signature_offset *= -1

          elif signature_offset > 0:
            if offset_mode == self.OFFSET_MODE_NEGATIVE:
              continue
            elif offset_mode == self.OFFSET_MODE_NEGATIVE_STRICT:
              raise ValueError(u'Signature offset greater than 0.')

          if signature_pattern_length < 4:
            raise ValueError(u'Signature pattern smaller than 4.')

          pattern = patterns.Pattern(
              signature_index, signature, specification)
          self.pattern_list.append(pattern)
          self.range_list.Insert(signature_offset, signature_pattern_length)

        signature_index += 1

  def _BuildScanTreeNode(self, pattern_table, ignore_list, is_bound):
    """Builds a scan tree node.

    Args:
      pattern_table: a pattern table (instance of PatternTable).
      ignore_list: a list of pattern offsets to ignore
      is_bound: boolean value to indicate if the signatures are bound
                to offsets. A value of None indicates that the value should
                be ignored and both bound and unbound patterns are considered
                unbound.

    Raises:
      ValueError: if number of byte value patterns value out of bounds.

    Returns:
      A scan tree node (instance of ScanTreeNode).
    """
    # Make a copy of the lists because the function is going to alter them
    # and the changes must remain in scope of the function.
    pattern_list = list(pattern_table.patterns)
    ignore_list = list(ignore_list)

    similarity_weights = _PatternWeights()
    occurrence_weights = _PatternWeights()
    value_weights = _PatternWeights()

    for pattern_offset in pattern_table.offsets:
      similarity_weights.AddOffset(pattern_offset)
      occurrence_weights.AddOffset(pattern_offset)
      value_weights.AddOffset(pattern_offset)

      byte_values = pattern_table.GetByteValues(pattern_offset)
      number_of_byte_values = len(byte_values)

      if number_of_byte_values > 1:
        occurrence_weights.SetWeight(pattern_offset, number_of_byte_values)

      for byte_value in byte_values:
        byte_value_patterns = byte_values[byte_value]
        byte_value_weight = len(byte_value_patterns.patterns)

        if byte_value_weight > 1:
          similarity_weights.AddWeight(pattern_offset, byte_value_weight)

        if not byte_value_weight in self._COMMON_BYTE_VALUES:
          value_weights.AddWeight(pattern_offset, 1)

    logging.debug(
        u'Pattern table:\n%s', pattern_table.ToDebugString())
    logging.debug(
        u'Similarity weights:\n%s', similarity_weights.ToDebugString())
    logging.debug(
        u'Occurrence weights:\n%s', occurrence_weights.ToDebugString())
    logging.debug(
        u'Value weights:\n%s', value_weights.ToDebugString())

    pattern_offset = self._GetMostSignificantPatternOffset(
        pattern_list, similarity_weights, occurrence_weights, value_weights)

    ignore_list.append(pattern_offset)

    scan_tree_node = ScanTreeNode(pattern_offset)

    byte_values = pattern_table.GetByteValues(pattern_offset)

    for byte_value in byte_values:
      byte_value_patterns = byte_values[byte_value]

      logging.debug(u'%s', byte_value_patterns.ToDebugString())

      number_of_byte_value_patterns = len(byte_value_patterns.patterns)

      if number_of_byte_value_patterns <= 0:
        raise ValueError(
            u'Invalid number of byte value patterns value out of bounds.')

      elif number_of_byte_value_patterns == 1:
        for identifier in byte_value_patterns.patterns:
          logging.debug(
              u'Adding pattern: {0:s} for byte value: 0x{1:02x}.'.format(
                  identifier, ord(byte_value)))

          scan_tree_node.AddByteValue(
              byte_value, byte_value_patterns.patterns[identifier])

      else:
        pattern_table = patterns.PatternTable(
            byte_value_patterns.patterns.itervalues(), ignore_list, is_bound)

        scan_sub_node = self._BuildScanTreeNode(
            pattern_table, ignore_list, is_bound)

        logging.debug(
            u'Adding scan node for byte value: 0x%02x\n%s',
            ord(byte_value), scan_sub_node.ToDebugString())

        scan_tree_node.AddByteValue(ord(byte_value), scan_sub_node)

      for identifier in byte_value_patterns.patterns:
        logging.debug(
            u'Removing pattern: %s from:\n%s', identifier,
            self._PatternsToDebugString(pattern_list))

        pattern_list.remove(byte_value_patterns.patterns[identifier])

    logging.debug(
        u'Remaining patterns:\n%s', self._PatternsToDebugString(pattern_list))

    number_of_patterns = len(pattern_list)

    if number_of_patterns == 1:
      logging.debug(
          u'Setting pattern: %s for default value', pattern_list[0].identifier)

      scan_tree_node.SetDefaultValue(pattern_list[0])

    elif number_of_patterns > 1:
      pattern_table = patterns.PatternTable(pattern_list, ignore_list, is_bound)

      scan_sub_node = self._BuildScanTreeNode(
          pattern_table, ignore_list, is_bound)

      logging.debug(
          u'Setting scan node for default value:\n%s',
          scan_sub_node.ToDebugString())

      scan_tree_node.SetDefaultValue(scan_sub_node)

    return scan_tree_node

  def _GetMostSignificantPatternOffset(
      self, pattern_list, similarity_weights, occurrence_weights,
      value_weights):
    """Returns the most significant pattern offset.

    Args:
      pattern_list: a list of patterns
      similarity_weights: the similarity (pattern) weights.
      occurrence_weights: the occurrence (pattern) weights.
      value_weights: the value (pattern) weights.

    Raises:
      ValueError: when pattern is an empty list.

    Returns:
      a pattern offset.
    """
    if not pattern_list:
      raise ValueError(u'Missing pattern list.')

    pattern_offset = None
    number_of_patterns = len(pattern_list)

    if number_of_patterns == 1:
      pattern_offset = self._GetPatternOffsetForValueWeights(
          value_weights)

    elif number_of_patterns == 2:
      pattern_offset = self._GetPatternOffsetForOccurrenceWeights(
          occurrence_weights, value_weights)

    elif number_of_patterns > 2:
      pattern_offset = self._GetPatternOffsetForSimilarityWeights(
          similarity_weights, occurrence_weights, value_weights)

    logging.debug(u'Largest weight offset: {0:d}'.format(pattern_offset))

    return pattern_offset

  def _GetPatternOffsetForOccurrenceWeights(
      self, occurrence_weights, value_weights):
    """Returns the most significant pattern offset based on the value weights.

    Args:
      occurrence_weights: the occurrence (pattern) weights.
      value_weights: the value (pattern) weights.

    Returns:
      a pattern offset.
    """
    debug_string = ""
    pattern_offset = None

    largest_weight = occurrence_weights.GetLargestWeight()
    logging.debug(u'Largest occurrence weight: {0:d}'.format(largest_weight))

    if largest_weight > 0:
      occurrence_weight_offsets = occurrence_weights.GetOffsetsForWeight(
          largest_weight)
      number_of_occurrence_offsets = len(occurrence_weight_offsets)
    else:
      number_of_occurrence_offsets = 0

    if number_of_occurrence_offsets == 0:
      pattern_offset = self._GetPatternOffsetForValueWeights(
          value_weights)

    elif number_of_occurrence_offsets == 1:
      pattern_offset = occurrence_weight_offsets[0]

    else:
      largest_weight = 0
      largest_value_weight = 0

      for occurrence_offset in occurrence_weight_offsets:
        value_weight = value_weights.GetWeightForOffset(
            occurrence_offset)

        debug_string = (
            u'Occurrence offset: %{0:d} value weight: %{1:d}').format(
                occurrence_offset, value_weight)

        if not pattern_offset or largest_weight < value_weight:
          largest_weight = value_weight
          pattern_offset = occurrence_offset

          debug_string += u' largest value weight: {0:d}'.format(
              largest_value_weight)

        logging.debug(u'{0:s}'.format(debug_string))

    return pattern_offset

  def _GetPatternOffsetForSimilarityWeights(
      self, similarity_weights, occurrence_weights, value_weights):
    """Returns the most significant pattern offset.

    Args:
      similarity_weights: the similarity (pattern) weights.
      occurrence_weights: the occurrence (pattern) weights.
      value_weights: the value (pattern) weights.

    Returns:
      a pattern offset.
    """
    debug_string = ""
    pattern_offset = None

    largest_weight = similarity_weights.GetLargestWeight()
    logging.debug(u'Largest similarity weight: %d', largest_weight)

    if largest_weight > 0:
      similarity_weight_offsets = similarity_weights.GetOffsetsForWeight(
          largest_weight)
      number_of_similarity_offsets = len(similarity_weight_offsets)
    else:
      number_of_similarity_offsets = 0

    if number_of_similarity_offsets == 0:
      pattern_offset = self._GetPatternOffsetForOccurrenceWeights(
          occurrence_weights, value_weights)

    elif number_of_similarity_offsets == 1:
      pattern_offset = similarity_weight_offsets[0]

    else:
      largest_weight = 0
      largest_value_weight = 0

      for similarity_offset in similarity_weight_offsets:
        occurrence_weight = occurrence_weights.GetWeightForOffset(
            similarity_offset)

        debug_string = (
            u'Similarity offset: %{0:d} occurrence weight: %{1:d}').format(
                similarity_offset, occurrence_weight)

        if largest_weight > 0 and largest_weight == occurrence_weight:
          value_weight = value_weights.GetWeightForOffset(
              similarity_offset)

          debug_string += u' value weight: {0:d}'.format(value_weight)

          if largest_value_weight < value_weight:
            largest_weight = 0

        if not pattern_offset or largest_weight < occurrence_weight:
          largest_weight = occurrence_weight
          pattern_offset = similarity_offset

          largest_value_weight = value_weights.GetWeightForOffset(
              similarity_offset)

          debug_string += u' largest value weight: {0:d}'.format(
              largest_value_weight)

        logging.debug(u'{0:s}'.format(debug_string))

    return pattern_offset

  def _GetPatternOffsetForValueWeights(
      self, value_weights):
    """Returns the most significant pattern offset based on the value weights.

    Args:
      value_weights: the value (pattern) weights.

    Raises:
      RuntimeError: no value weight offset were found.

    Returns:
      a pattern offset.
    """
    largest_weight = value_weights.GetLargestWeight()
    logging.debug(u'Largest value weight: {0:d}'.format(largest_weight))

    if largest_weight > 0:
      value_weight_offsets = value_weights.GetOffsetsForWeight(largest_weight)
      number_of_value_offsets = len(value_weight_offsets)
    else:
      number_of_value_offsets = 0

    if number_of_value_offsets == 0:
      raise RuntimeError(u'No value weight offsets found.')

    return value_weight_offsets[0]

  def _PatternsToDebugString(self, pattern_list):
    """Converts the list of patterns into a debug string."""
    entries = u', '.join([u'{0:s}'.format(pattern) for pattern in pattern_list])

    return u''.join([u'[', entries, u']'])


class ScanTreeNode(object):
  """Class that implements a scan tree node."""

  def __init__(self, pattern_offset):
    """Initializes the scan tree node.

    Args:
      pattern_offset: the offset in the pattern to which the node
                      applies.
    """
    super(ScanTreeNode, self).__init__()
    self._byte_values = {}
    self.default_value = None
    self.parent = None
    self.pattern_offset = pattern_offset

  def AddByteValue(self, byte_value, scan_object):
    """Adds a byte value.

    Args:
      byte_value:  the corresponding byte value.
      scan_object: the scan object, either a scan sub node or a pattern.

    Raises:
      ValueError: if byte value is out of bounds or if the node already
                  contains a scan object for the byte value.
    """
    if isinstance(byte_value, str):
      byte_value = ord(byte_value)

    if byte_value < 0 or byte_value > 255:
      raise ValueError(u'Invalid byte value, value out of bounds.')

    if byte_value in self._byte_values:
      raise ValueError(u'Byte value already set.')

    if isinstance(scan_object, ScanTreeNode):
      scan_object.parent = self

    self._byte_values[byte_value] = scan_object

  def CompareByteValue(self, data, data_size, data_offset, match_on_boundary):
    """Scans a buffer using the bounded scan tree.

    Args:
      data: a buffer containing raw data.
      data_size: the size of the raw data in the buffer.
      data_offset: the offset in the raw data in the buffer.
      match_on_boundary: boolean value to indicate if a match on data boundary
                         is permitted.

    Raises:
      RuntimeError: if the data offset is out of bounds.

    Returns:
      the resulting scan object which is either a ScanTreeNode or Pattern
      or None.
    """
    found_match = False
    scan_tree_byte_value = 0

    if data_offset < 0 or data_offset >= data_size:
      raise RuntimeError(u'Data offset out of bounds.')

    data_offset += self.pattern_offset

    if not match_on_boundary and data_offset >= data_size:
      raise RuntimeError(u'Pattern offset out of bounds.')

    if data_offset < data_size:
      data_byte_value = ord(data[data_offset])

      for scan_tree_byte_value in self._byte_values:
        if data_byte_value == scan_tree_byte_value:
          found_match = True
          break

    if found_match:
      scan_object = self._byte_values[scan_tree_byte_value]
    else:
      scan_object = self.default_value
      if not scan_object:
        scan_object = self.parent
        while scan_object and not scan_object.default_value:
          scan_object = scan_object.parent

        if scan_object:
          scan_object = scan_object.default_value

    return scan_object

  def SetDefaultValue(self, scan_object):
    """Sets the default (non-match) value.

    Args:
      scan_object: the scan object, either a scan sub node or a pattern.

    Raises:
      ValueError: if the default value is already set.
    """
    if self.default_value:
      raise ValueError(u'Default value already set.')

    self.default_value = scan_object

  def ToDebugString(self, indentation_level=1):
    """Converts the scan tree node into a debug string."""
    indentation = u'  ' * indentation_level

    header = u'{0:s}pattern offset: {1:d}\n'.format(
        indentation, self.pattern_offset)

    entries = u''

    for byte_value in self._byte_values:
      entries += u'{0:s}byte value: 0x{1:02x}\n'.format(indentation, byte_value)

      if isinstance(self._byte_values[byte_value], ScanTreeNode):
        entries += u'{0:s}scan tree node:\n'.format(indentation)
        entries += self._byte_values[byte_value].ToDebugString(
            indentation_level + 1)

      elif isinstance(self._byte_values[byte_value], patterns.Pattern):
        entries += u'{0:s}pattern: {1:s}\n'.format(
            indentation, self._byte_values[byte_value].identifier)

    default = u'{0:s}default value:\n'.format(indentation)

    if isinstance(self.default_value, ScanTreeNode):
      default += u'{0:s}scan tree node:\n'.format(indentation)
      default += self.default_value.ToDebugString(indentation_level + 1)

    elif isinstance(self.default_value, patterns.Pattern):
      default += u'{0:s}pattern: {1:s}\n'.format(
          indentation, self.default_value.identifier)

    return u''.join([header, entries, default, u'\n'])
