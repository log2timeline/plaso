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
"""This file contains the classes for a scan tree-based format scanner."""
import logging


class _ByteValuePatterns(object):
  """Class that contains the relationship specific byte value and patterns.

  The class is intended to be used internally in the scanner and maps
  a byte value with one or more patterns.
  """

  def __init__(self, byte_value):
    """Initializes the pattern table (entry) byte value.

    Args:
      byte_value: the byte value that maps the patterns in the table.
    """
    self.byte_value = byte_value
    self.patterns = {}

  def __str__(self):
    """Retrieves a string representation of the byte value patterns."""
    return "0x{0:02x} {1!s}".format(ord(self.byte_value), self.patterns)

  def AddPattern(self, pattern):
    """Adds a pattern.

    Args:
      pattern: an instance of Pattern.

    Raises:
      ValueError: if the table entry already contains a pattern
                  with the same identifier.
    """
    if pattern.identifier in self.patterns:
      raise ValueError("pattern {0:s} is already defined.".format(
          pattern.identifier))

    self.patterns[pattern.identifier] = pattern

  def ToDebugString(self, indentation_level=1):
    """Converts the byte value pattern into a debug string."""
    indentation = u"  " * indentation_level

    header = u"{0:s}byte value: 0x{1:02x}\n".format(
        indentation, ord(self.byte_value))

    entries = u"".join([u"{0:s}  patterns: {1:s}\n".format(
        indentation, identifier) for identifier in self.patterns])

    return u"".join([header, entries, u"\n"])


class Pattern(object):
  """Class that contains a pattern."""

  def __init__(self, signature_index, signature, specification):
    """Initializes the pattern.

    Args:
      signature_index: the index of the signature within the specification.
      signature: an instance of _Signature that contains the signature.
      specification: an instance of Specification or the specification that
                     contains the signature.
    """
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
    # Using _ here because re2 only allows for a limited character set
    # for the identifiers
    return "{0:s}_{1:d}".format(
        self.specification.identifier, self._signature_index)

  @property
  def is_bound(self):
    """Boolean value to indicate the signature is bound to an offset."""
    return self.signature.is_bound


class PatternTable(object):
  """Class that contains a pattern table."""

  def __init__(self, patterns, ignore_list, is_bound):
    """Initializes and builds the patterns table from patterns.

    The class is intended to be used internally in the scanner to help
    in constructing the bound and unbound scanning trees. It
    contains either bound or unbound patterns.

    Args:
      patterns: a list of the patterns.
      ignore_list: a list of pattern offsets to ignore.
      is_bound: boolean value to indicate if the signatures should have bound
                offsets.

    Raises:
      ValueError: if a signature pattern is too small to be useful (< 4)
    """
    self._byte_values_per_offset = {}
    self.patterns = []
    self.largest_pattern_length = 0
    self.smallest_pattern_length = 0

    for pattern in patterns:
      if pattern.signature.is_bound != is_bound:
        continue

      pattern_length = len(pattern.expression)

      if pattern_length < 4:
        raise ValueError("pattern too small to be useful")

      self.smallest_pattern_length = min(
          self.smallest_pattern_length, pattern_length)

      self.largest_pattern_length = max(
          self.largest_pattern_length, pattern_length)

      self.patterns.append(pattern)

      self._AddPattern(pattern, ignore_list, is_bound)

  @property
  def offsets(self):
    """The offsets."""
    return self._byte_values_per_offset.keys()

  def _AddPattern(self, pattern, ignore_list, is_bound):
    """Addes the byte values per offset in the pattern to the table.

    Args:
      pattern: an instance of Pattern.
      ignore_list: a list of pattern offsets to ignore.
      is_bound: boolean value to indicate if the signatures should have bound
                offsets.
    """
    pattern_offset = pattern.signature.offset if is_bound else 0

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

  def GetByteValues(self, pattern_offset):
    """Returns the bytes values for a specific pattern offset."""
    return self._byte_values_per_offset[pattern_offset]

  def GetSkipTable(self):
    """Retrieves the skip table for the patterns in the table.

    Returns:
      an instance of _SkipTable.
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
    header = u"pattern offset\tbyte value(s)\n"
    entries = u""

    for pattern_offset in self._byte_values_per_offset:
      entries += u"{0:d}".format(pattern_offset)

      byte_values = self._byte_values_per_offset[pattern_offset]

      for byte_value in byte_values:
        identifiers = u", ".join(
            [identifier for identifier in byte_values[byte_value].patterns])

        entries += u"\t0x{0:02x} ({1:s})".format(ord(byte_value), identifiers)

      entries += u"\n"

    return u"".join([header, entries, u"\n"])


class _PatternWeights(object):
  """Class that contains a pattern weights."""

  def __init__(self):
    """Initializes the pattern weights."""
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
      raise ValueError("pattern offset already set")

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
      raise ValueError("pattern offset not set")

    self._weight_per_offset[pattern_offset] += weight

    if not weight in self._offsets_per_weight:
      self._offsets_per_weight[weight] = []

    self._offsets_per_weight[weight].append(pattern_offset)

  def SetWeight(self, pattern_offset, weight):
    """Sets a weight for a specific pattern offset.

    Args:
      pattern_offset: the pattern offset to set in the pattern weights.
      weight: the corresponding weight to set.

    Raises:
      ValueError: if the pattern weights does not contain the pattern offset.
    """
    if not pattern_offset in self._weight_per_offset:
      raise ValueError("pattern offset not set")

    self._weight_per_offset[pattern_offset] = weight

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
    header1 = u"pattern offset\tweight\n"

    entries1 = u"".join([u"{0:d}\t{1:d}\n".format(
        pattern_offset, self._weight_per_offset[pattern_offset])
                         for pattern_offset in self._weight_per_offset])

    header2 = u"weight\tpattern offset(s)\n"

    entries2 = u"".join([u"{0:d}\t{1!s}\n".format(
        weight, self._offsets_per_weight[weight])
                         for weight in self._offsets_per_weight])

    return u"".join([header1, entries1, u"\n", header2, entries2, u"\n"])


class ScanState(object):
  """Class that contains state information for the scanner."""

  # The state definitions
  START = 1
  SCANNING = 2
  STOP = 3

  def __init__(self, scan_tree_node):
    """Initializes the scan state.

    Args:
      scan_tree_node: the corresponding scan tree node or None.
    """
    self._results = []
    self.file_offset = 0
    self.scan_tree_node = scan_tree_node
    self.state = self.START

    self.remaining_data = None
    self.remaining_data_size = 0

  def AddResult(self, file_offset, pattern):
    """Adds a result to the state to scanning.

    Args:
      file_offset: the offset of the resulting match relative to the start
                   of the file.
      pattern: the pattern matched.
    """
    self._results.append(_ScanResult(file_offset, pattern))

  def GetResults(self):
    """Retrieves a list containing the results."""
    return self._results

  def Scanning(self, file_offset, scan_tree_node):
    """Sets the state to scanning.

    Args:
      file_offset: the offset of the resulting match relative to the start
                   of the file.
      scan_tree_node: the active scan tree node.

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if self.state != self.START and self.state != self.SCANNING:
      raise RuntimeError("Unsupported scan state")

    self.file_offset = file_offset
    self.scan_tree_node = scan_tree_node
    self.state = self.SCANNING

  def Stop(self):
    """Sets the state to stop.

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if self.state != self.START and self.state != self.SCANNING:
      raise RuntimeError("Unsupported scan state")

    self.scan_tree_node = None
    self.state = self.STOP


class _ScanResult(object):
  """Class that contains result for the scanner."""

  def __init__(self, file_offset, pattern):
    """Initializes the scan result.

    Args:
      file_offset: the offset of the resulting match relative to the start
                   of the file.
      pattern: the pattern matched.
    """
    self.file_offset = file_offset
    self.pattern = pattern

  @property
  def specification(self):
    """The specification."""
    return self.pattern.specification


class _ScanTreeNode(object):
  """Class that represents a node in the scanning tree."""

  def __init__(self, pattern_offset):
    """Initializes the scan tree node.

    Args:
      pattern_offset: the offset in the pattern to which the node
                      applies.
    """
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
      raise ValueError("invalid byte value, value out of bounds")

    if byte_value in self._byte_values:
      raise ValueError("byte value already set")

    if isinstance(scan_object, _ScanTreeNode):
      scan_object.parent = self

    self._byte_values[byte_value] = scan_object

  def SetDefaultValue(self, scan_object):
    """Sets the default (non-match) value.

    Args:
      scan_object: the scan object, either a scan sub node or a pattern.

    Raises:
      ValueError: if the default value is already set.
    """
    if self.default_value:
      raise ValueError("default value already set")

    self.default_value = scan_object

  def ToDebugString(self, indentation_level=1):
    """Converts the scan tree node into a debug string."""
    indentation = u"  " * indentation_level

    header = u"{0:s}pattern offset: {1:d}\n".format(
        indentation, self.pattern_offset)

    entries = u""

    for byte_value in self._byte_values:
      entries += u"{0:s}byte value: 0x{1:02x}\n".format(indentation, byte_value)

      if isinstance(self._byte_values[byte_value], _ScanTreeNode):
        entries += u"{0:s}scan tree node:\n".format(indentation)
        entries += self._byte_values[byte_value].ToDebugString(
            indentation_level + 1)

      elif isinstance(self._byte_values[byte_value], Pattern):
        entries += u"{0:s}pattern: {1:s}\n".format(
            indentation, self._byte_values[byte_value].identifier)

    default = u"{0:s}default value:\n".format(indentation)

    if isinstance(self.default_value, _ScanTreeNode):
      default += u"{0:s}scan tree node:\n".format(indentation)
      default += self.default_value.ToDebugString(indentation_level + 1)

    elif isinstance(self.default_value, Pattern):
      default += "{0:s}pattern: {1:s}\n".format(
          indentation, self.default_value.identifier)

    return u"".join([header, entries, default, u"\n"])

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
      the resulting scan object which is either a _ScanTreeNode or Pattern
      or None.
    """
    found_match = False
    scan_tree_byte_value = 0

    if data_offset < 0 or data_offset >= data_size:
      raise RuntimeError("data offset out of bounds")

    data_offset += self.pattern_offset

    if not match_on_boundary and data_offset >= data_size:
      raise RuntimeError("pattern offset out of bounds")

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


class _SkipTable(object):
  """Class that contains skip table for the scanner."""

  def __init__(self, skip_pattern_length):
    """Initializes the skip table.

    Args:
      skip_pattern_length: the (maximum) skip pattern length.
    """
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
      raise ValueError("invalid byte value, value out of bounds")

    if skip_value < 0 or skip_value >= self.skip_pattern_length:
      raise ValueError("invalid skip value, value out of bounds")

    if (not byte_value in self._skip_value_per_byte_value or
        self._skip_value_per_byte_value[byte_value] > skip_value):
      self._skip_value_per_byte_value[byte_value] = skip_value

  def ToDebugString(self):
    """Converts the skip table into a debug string."""
    header = u"byte value\tskip value\n"

    entries = u"".join([u"0x{0:02x}\t{1:d}\n".format(
        byte_value, self._skip_value_per_byte_value[byte_value])
                        for byte_value in self._skip_value_per_byte_value])

    default = u"default\t{0:d}\n".format(self.skip_pattern_length)

    return u"".join([header, entries, default, u"\n"])


class Scanner(object):
  """Class for scanning for formats in raw data."""

  COMMON_BYTE_VALUES = frozenset(
      "\x00\x01\xff\t\n\r 0123456789"
      "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
      "abcdefghijklmnopqrstuvwxyz")

  def __init__(self, specification_store):
    """Initializes the scanner and sets up the scanning related structures.

    Args:
      specification_store: an instance of SpecifiCationStore that contains
                           the format specifications.
    """
    self._bound_scan_tree = None
    self._scan_tree = None
    self._scan_tree_largest_length = 0
    self._skip_table = None

    self._BuildScanningTrees(specification_store)

  def _BuildPatterns(self, specification_store):
    """Builds the list of patterns.

    Args:
      specification_store: an instance of SpecifiCationStore that contains
                           the format specifications.

    Returns:
      a list of patterns.

    Raises:
      ValueError: if a signature pattern is too small to be useful (< 4)
    """
    patterns = []

    for specification in specification_store.specifications:
      signature_index = 0

      for signature in specification.signatures:
        if signature.expression:
          signature_pattern_length = len(signature.expression)

          if signature_pattern_length < 4:
            raise ValueError("pattern too small to be useful")

          pattern = Pattern(signature_index, signature, specification)
          patterns.append(pattern)
        signature_index += 1

    return patterns

  def _BuildScanningTrees(self, specification_store):
    """Builds the scanning trees.

    Args:
      specification_store: an instance of SpecifiCationStore that contains
                           the format specifications.
    """
    # First determine all the patterns from the specification store
    patterns = self._BuildPatterns(specification_store)

    # Next 2 scanning trees are created one for offset-bound patterns
    # another one for unbound patterns
    ignore_list = []
    is_bound = True
    pattern_table = PatternTable(patterns, ignore_list, is_bound)

    self._bound_scan_tree = self._BuildScanTreeNode(
        pattern_table, ignore_list, is_bound)

    logging.debug("bound scan tree:\n%s",
                  self._bound_scan_tree.ToDebugString())

    ignore_list = []
    is_bound = False
    pattern_table = PatternTable(patterns, ignore_list, is_bound)

    self._scan_tree = self._BuildScanTreeNode(
        pattern_table, ignore_list, is_bound)

    logging.debug("scan tree:\n%s",
                  self._scan_tree.ToDebugString())

    # At the end the skip table is determined to provide for the
    # Boyer–Moore–Horspool skip value
    self._skip_table = pattern_table.GetSkipTable()

    logging.debug("skip table:\n%s",
                  self._skip_table.ToDebugString())

    self._scan_tree_largest_length = pattern_table.largest_pattern_length

  def _PatternsToDebugString(self, patterns):
    """Converts the patterns into a debug string."""
    entries = u", ".join([u"{0:s}".format(pattern) for pattern in patterns])

    return u"".join([u"[", entries, u"]"])

  def _BuildScanTreeNode(self, patterns_table, ignore_list, is_bound):
    """Builds a scan tree node.

    Args:
      patterns_table: an instance of PatternTable.
      ignore_list: a list of pattern offsets to ignore
      is_bound: boolean value to indicate if the signatures should have bound
                offsets.

    Raises:
      ValueError: if number of byte value patterns value out of bounds.

    Returns:
      a scan tree node.
    """
    # Make a copy of the lists because the function is going to alter them
    # and the changes must remain in scope of the function
    patterns = list(patterns_table.patterns)
    ignore_list = list(ignore_list)

    similarity_weights = _PatternWeights()
    occurrence_weights = _PatternWeights()
    value_weights = _PatternWeights()

    for pattern_offset in patterns_table.offsets:
      similarity_weights.AddOffset(pattern_offset)
      occurrence_weights.AddOffset(pattern_offset)
      value_weights.AddOffset(pattern_offset)

      byte_values = patterns_table.GetByteValues(pattern_offset)
      number_of_byte_values = len(byte_values)

      if number_of_byte_values > 1:
        occurrence_weights.SetWeight(pattern_offset, number_of_byte_values)

      for byte_value in byte_values:
        byte_value_patterns = byte_values[byte_value]
        byte_value_weight = len(byte_value_patterns.patterns)

        if byte_value_weight > 1:
          similarity_weights.AddWeight(pattern_offset, byte_value_weight)

        if not byte_value_weight in self.COMMON_BYTE_VALUES:
          value_weights.AddWeight(pattern_offset, 1)

    logging.debug("patterns table:\n%s", patterns_table.ToDebugString())
    logging.debug("similarity weights:\n%s",
                  similarity_weights.ToDebugString())
    logging.debug("occurrence weights:\n%s",
                  occurrence_weights.ToDebugString())
    logging.debug("value weights:\n%s", value_weights.ToDebugString())

    pattern_offset = self._GetMostSignificantPatternOffset(
        patterns, similarity_weights, occurrence_weights, value_weights)

    ignore_list.append(pattern_offset)

    scan_tree_node = _ScanTreeNode(pattern_offset)

    byte_values = patterns_table.GetByteValues(pattern_offset)

    for byte_value in byte_values:
      byte_value_patterns = byte_values[byte_value]

      logging.debug("%s", byte_value_patterns.ToDebugString())

      number_of_byte_value_patterns = len(byte_value_patterns.patterns)

      if number_of_byte_value_patterns <= 0:
        raise ValueError(
            "invalid number of byte value patterns value out of bounds")

      elif number_of_byte_value_patterns == 1:
        for identifier in byte_value_patterns.patterns:
          logging.debug("adding pattern: %s for byte value: 0x%02x",
                        identifier, ord(byte_value))

          scan_tree_node.AddByteValue(
              byte_value, byte_value_patterns.patterns[identifier])

      else:
        pattern_table = PatternTable(
            byte_value_patterns.patterns.values(), ignore_list, is_bound)

        scan_sub_node = self._BuildScanTreeNode(
            pattern_table, ignore_list, is_bound)

        logging.debug("adding scan node for byte value: 0x%02x\n%s",
                      ord(byte_value), scan_sub_node.ToDebugString())

        scan_tree_node.AddByteValue(ord(byte_value), scan_sub_node)

      for identifier in byte_value_patterns.patterns:
        logging.debug("removing pattern: %s from:\n%s", identifier,
                      self._PatternsToDebugString(patterns))

        patterns.remove(byte_value_patterns.patterns[identifier])

    logging.debug("Remaining patterns:\n%s",
                  self._PatternsToDebugString(patterns))

    number_of_patterns = len(patterns)

    if number_of_patterns == 1:
      logging.debug("setting pattern: %s for default value",
                    patterns[0].identifier)

      scan_tree_node.SetDefaultValue(patterns[0])

    elif number_of_patterns > 1:
      pattern_table = PatternTable(patterns, ignore_list, is_bound)

      scan_sub_node = self._BuildScanTreeNode(
          pattern_table, ignore_list, is_bound)

      logging.debug("setting scan node for default value:\n%s",
                    scan_sub_node.ToDebugString())

      scan_tree_node.SetDefaultValue(scan_sub_node)

    return scan_tree_node

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
    logging.debug("largest similarity weight: %d", largest_weight)

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

        debug_string = ("similarity offset: %{0:d} occurrence weight: "
                        "%{1:d}").format(similarity_offset, occurrence_weight)

        if largest_weight > 0 and largest_weight == occurrence_weight:
          value_weight = value_weights.GetWeightForOffset(
              similarity_offset)

          debug_string += " value weight: {0:d}".format(value_weight)

          if largest_value_weight < value_weight:
            largest_weight = 0

        if not pattern_offset or largest_weight < occurrence_weight:
          largest_weight = occurrence_weight
          pattern_offset = similarity_offset

          largest_value_weight = value_weights.GetWeightForOffset(
              similarity_offset)

          debug_string += " largest value weight: {0:d}".format(
              largest_value_weight)

        logging.debug("%s", debug_string)

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
    logging.debug("largest occurrence weight: %d", largest_weight)

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

        debug_string = ("occurrence offset: %{0:d} value weight: "
                        "%{1:d}").format(occurrence_offset, value_weight)

        if not pattern_offset or largest_weight < value_weight:
          largest_weight = value_weight
          pattern_offset = occurrence_offset

          debug_string += " largest value weight: {0:d}".format(
              largest_value_weight)

        logging.debug("%s", debug_string)

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
    logging.debug("largest value weight: %d", largest_weight)

    if largest_weight > 0:
      value_weight_offsets = value_weights.GetOffsetsForWeight(largest_weight)
      number_of_value_offsets = len(value_weight_offsets)
    else:
      number_of_value_offsets = 0

    if number_of_value_offsets == 0:
      raise RuntimeError("No value weight offsets found")

    return value_weight_offsets[0]

  def _GetMostSignificantPatternOffset(
      self, patterns, similarity_weights, occurrence_weights, value_weights):
    """Returns the most significant pattern offset.

    Args:
      patterns: a list of patterns
      similarity_weights: the similarity (pattern) weights.
      occurrence_weights: the occurrence (pattern) weights.
      value_weights: the value (pattern) weights.

    Raises:
      ValueError: when pattern is an empty list.

    Returns:
      a pattern offset.
    """
    if not patterns:
      raise ValueError("missing patterns")

    pattern_offset = None
    number_of_patterns = len(patterns)

    if number_of_patterns == 1:
      pattern_offset = self._GetPatternOffsetForValueWeights(
          value_weights)

    elif number_of_patterns == 2:
      pattern_offset = self._GetPatternOffsetForOccurrenceWeights(
          occurrence_weights, value_weights)

    elif number_of_patterns > 2:
      pattern_offset = self._GetPatternOffsetForSimilarityWeights(
          similarity_weights, occurrence_weights, value_weights)

    logging.debug("largest weight offset: %d", pattern_offset)

    return pattern_offset

  def ScanStart(self):
    """Starts a scan.

    Returns:
      a scan state.
    """
    return ScanState(self._scan_tree)

  def _ScanBufferBoundedScanTree(self, scan_state, file_offset, data,
                                 data_size):
    """Scans a buffer using the bounded scan tree.

    Args:
      scan_state: an instance of ScanState.
      file_offset: the offset of the data relative to the start of the file.
      data: a buffer containing raw data.
      data_size: the size of the raw data in the buffer.
    """
    scan_done = False
    scan_tree_node = self._bound_scan_tree

    while not scan_done:
      scan_object = scan_tree_node.CompareByteValue(data, data_size, 0, True)

      if isinstance(scan_object, _ScanTreeNode):
        scan_tree_node = scan_object
      else:
        scan_done = True

    if isinstance(scan_object, Pattern):
      pattern_length = len(scan_object.signature.expression)

      if cmp(scan_object.signature.expression,
             data[scan_object.signature.offset:pattern_length]) == 0:
        scan_state.AddResult(
            file_offset + scan_object.signature.offset, scan_object)

  def _ScanBufferScanState(self, scan_state, file_offset, data, data_size,
                           match_on_boundary):
    """Scans a buffer using the scan tree.

    This function implements a Boyer–Moore–Horspool equivalent approach
    in combination with the scan tree.

    Args:
      scan_state: an instance of ScanState.
      file_offset: the offset of the data relative to the start of the file.
      data: a buffer containing raw data.
      data_size: the size of the raw data in the buffer.
      match_on_boundary: boolean value to indicate if a match on data boundary
                         is permitted

    Raises:
      RuntimeError: if the last pattern offset is out of bounds
    """
    data_offset = 0
    scan_tree_node = scan_state.scan_tree_node

    if (scan_state.remaining_data and
        scan_state.file_offset + scan_state.remaining_data_size == file_offset):
      # str.join() should be more efficient then concatenation by +
      data = "".join([scan_state.remaining_data, data])
      data_size += scan_state.remaining_data_size

      scan_state.remaining_data = None
      scan_state.remaining_data_size = 0

    while data_offset < data_size:
      if (not match_on_boundary and
          data_offset + self._scan_tree_largest_length >= data_size):
        break

      found_match = False
      scan_done = False

      while not scan_done:
        scan_object = scan_tree_node.CompareByteValue(
            data, data_size, data_offset, match_on_boundary)

        if isinstance(scan_object, _ScanTreeNode):
          scan_tree_node = scan_object
        else:
          scan_done = True

      if isinstance(scan_object, Pattern):
        pattern_length = len(scan_object.signature.expression)

        data_last_offset = data_offset + pattern_length
        if cmp(scan_object.signature.expression,
               data[data_offset:data_last_offset]) == 0:

          if (not scan_object.signature.is_bound or
              scan_object.signature.offset == data_offset):
            found_match = True

            scan_state.AddResult(file_offset + data_offset, scan_object)

      if found_match:
        skip_value = len(scan_object.signature.expression)
        scan_tree_node = self._scan_tree
      else:
        last_pattern_offset = self._skip_table.skip_pattern_length - 1

        if data_offset + last_pattern_offset >= data_size:
          raise RuntimeError("last pattern offset out of bounds")
        skip_value = 0

        while last_pattern_offset >= 0 and not skip_value:
          last_data_offset = data_offset + last_pattern_offset
          byte_value = ord(data[last_data_offset])
          skip_value = self._skip_table[byte_value]
          last_pattern_offset -= 1

        if not skip_value:
          skip_value = 1

        scan_tree_node = self._scan_tree

      data_offset += skip_value

    if not match_on_boundary and data_offset < data_size:
      scan_state.remaining_data = data[data_offset:data_size]
      scan_state.remaining_data_size = data_size - data_offset

    scan_state.Scanning(scan_state.file_offset + data_offset, scan_tree_node)

  def _ScanBufferScanStateFinal(self, scan_state):
    """Scans the remaining data in the scan state using the scan tree.

    Args:
      scan_state: an instance of ScanState.
    """
    if scan_state.remaining_data:
      data = scan_state.remaining_data
      data_size = scan_state.remaining_data_size

      scan_state.remaining_data = None
      scan_state.remaining_data_size = 0

      self._ScanBufferScanState(
          scan_state, scan_state.file_offset, data, data_size, True)

    scan_state.Stop()

  def ScanBuffer(self, scan_state, file_offset, data):
    """Scans a buffer.

    Args:
      scan_state: an instance of ScanState.
      file_offset: the offset of the data relative to the start of the file.
      data: a buffer containing raw data.
    """
    data_size = len(data)

    if file_offset == 0:
      self._ScanBufferBoundedScanTree(scan_state, file_offset, data, data_size)

    self._ScanBufferScanState(scan_state, file_offset, data, data_size, False)

  def ScanStop(self, scan_state):
    """Stops a scan.

    Args:
      scan_state: an instance of ScanState.
    """
    self._ScanBufferScanStateFinal(scan_state)
