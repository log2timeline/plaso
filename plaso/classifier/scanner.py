#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The PyVFS Project Authors.
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
"""This file contains the classes for a scan tree-based format scanner."""

import os

from plaso.classifier import patterns
from plaso.classifier import scan_tree


class _ScanResult(object):
  """Class that implements scan results."""

  def __init__(self, file_offset, pattern):
    """Initializes the scan result.

    Args:
      file_offset: the offset of the resulting match relative to the start
                   of the file.
      pattern: the pattern matched.
    """
    super(_ScanResult, self).__init__()
    self.file_offset = file_offset
    self.pattern = pattern

  @property
  def specification(self):
    """The specification."""
    return self.pattern.specification


class ScanState(object):
  """Class that implements a scan state."""

  # The state definitions.
  START = 1
  SCANNING = 2
  STOP = 3

  def __init__(self, scan_tree_node):
    """Initializes the scan state.

    Args:
      scan_tree_node: the corresponding scan tree node or None.
    """
    super(ScanState, self).__init__()
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
      raise RuntimeError(u'Unsupported scan state.')

    self.file_offset = file_offset
    self.scan_tree_node = scan_tree_node
    self.state = self.SCANNING

  def Stop(self):
    """Sets the state to stop.

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if self.state != self.START and self.state != self.SCANNING:
      raise RuntimeError(u'Unsupported scan state.')

    self.scan_tree_node = None
    self.state = self.STOP


class Scanner(object):
  """Class that implements a scan tree-based scanner."""

  _READ_BUFFER_SIZE = 512

  def __init__(self, specification_store):
    """Initializes the scanner.

    Args:
      specification_store: the specification store (instance of
                           SpecificationStore) that contains the format
                           specifications.
    """
    super(Scanner, self).__init__()
    self._scan_tree = None
    self._specification_store = specification_store

  def _ScanBufferScanState(
      self, scan_tree_object, scan_state, file_offset, data, data_size,
      match_on_boundary):
    """Scans a buffer using the scan tree.

    This function implements a Boyer–Moore–Horspool equivalent approach
    in combination with the scan tree.

    Args:
      scan_tree_object: the scan tree (instance of ScanTree).
      scan_state: the scan state (instance of ScanState).
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
      # str.join() should be more efficient then concatenation by +.
      data = "".join([scan_state.remaining_data, data])
      data_size += scan_state.remaining_data_size

      scan_state.remaining_data = None
      scan_state.remaining_data_size = 0

    while data_offset < data_size:
      if (not match_on_boundary and
          data_offset + scan_tree_object.largest_length >= data_size):
        break

      found_match = False
      scan_done = False

      while not scan_done:
        scan_object = scan_tree_node.CompareByteValue(
            data, data_size, data_offset, match_on_boundary)

        if isinstance(scan_object, scan_tree.ScanTreeNode):
          scan_tree_node = scan_object
        else:
          scan_done = True

      if isinstance(scan_object, patterns.Pattern):
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
        scan_tree_node = scan_tree_object.root_node
      else:
        last_pattern_offset = (
            scan_tree_object.skip_table.skip_pattern_length - 1)

        if data_offset + last_pattern_offset >= data_size:
          raise RuntimeError(u'Last pattern offset out of bounds.')
        skip_value = 0

        while last_pattern_offset >= 0 and not skip_value:
          last_data_offset = data_offset + last_pattern_offset
          byte_value = ord(data[last_data_offset])
          skip_value = scan_tree_object.skip_table[byte_value]
          last_pattern_offset -= 1

        if not skip_value:
          skip_value = 1

        scan_tree_node = scan_tree_object.root_node

      data_offset += skip_value

    if not match_on_boundary and data_offset < data_size:
      scan_state.remaining_data = data[data_offset:data_size]
      scan_state.remaining_data_size = data_size - data_offset

    scan_state.Scanning(scan_state.file_offset + data_offset, scan_tree_node)

  def _ScanBufferScanStateFinal(self, scan_state):
    """Scans the remaining data in the scan state using the scan tree.

    Args:
      scan_state: the scan state (instance of ScanState).
    """
    if scan_state.remaining_data:
      data = scan_state.remaining_data
      data_size = scan_state.remaining_data_size

      scan_state.remaining_data = None
      scan_state.remaining_data_size = 0

      self._ScanBufferScanState(
          self._scan_tree, scan_state, scan_state.file_offset, data, data_size,
          True)

    scan_state.Stop()

  def ScanBuffer(self, scan_state, file_offset, data):
    """Scans a buffer.

    Args:
      scan_state: the scan state (instance of ScanState).
      file_offset: the offset of the data relative to the start of the file.
      data: a buffer containing raw data.
    """
    data_size = len(data)
    self._ScanBufferScanState(
        self._scan_tree, scan_state, file_offset, data, data_size, False)

  def ScanFileObject(self, scan_state, file_offset, file_object):
    """Scans a file-like object.

    Args:
      scan_state: the scan state (instance of ScanState).
      file_offset: the offset of the data relative to the start of the file.
      file_object: a file-like object.
    """
    file_object.seek(file_offset, os.SEEK_SET)

    data = file_object.read(self._READ_BUFFER_SIZE)
    data_size = len(data)
    file_offset += data_size

    while data:
      self._ScanBufferScanState(
          self._scan_tree, scan_state, file_offset, data, data_size, True)
      data = file_object.read(self._READ_BUFFER_SIZE)
      data_size = len(data)
      file_offset += data_size

    self.ScanStop(scan_state)

  def ScanStart(self):
    """Starts a scan.

       The function sets up the scanning related structures if necessary.

    Returns:
      A scan state (instance of ScanState).
    """
    if self._scan_tree is None:
      self._scan_tree = scan_tree.ScanTree(
          self._specification_store, None)

    return ScanState(self._scan_tree.root_node)

  def ScanStop(self, scan_state):
    """Stops a scan.

    Args:
      scan_state: the scan state (instance of ScanState).
    """
    self._ScanBufferScanStateFinal(scan_state)
