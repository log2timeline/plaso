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
"""This file contains the classes for a scan tree-based format scanner."""

import logging
import os

from plaso.classifier import patterns
from plaso.classifier import range_list
from plaso.classifier import scan_tree


class _ScanMatch(object):
  """Class that implements a scan match."""

  def __init__(self, total_data_offset, pattern):
    """Initializes the scan result.

    Args:
      total_data_offset: the offset of the resulting match relative
                         to the start of the total data scanned.
      pattern: the pattern matched.
    """
    super(_ScanMatch, self).__init__()
    self.total_data_offset = total_data_offset
    self.pattern = pattern

  @property
  def specification(self):
    """The specification."""
    return self.pattern.specification


class _ScanResult(object):
  """Class that implements a scan result."""

  def __init__(self, specification):
    """Initializes the scan result.

    Args:
      scan_tree_node: the corresponding scan tree node or None.
    """
    super(_ScanResult, self).__init__()
    self.specification = specification
    self.scan_matches = []

  @property
  def identifier(self):
    """The specification identifier."""
    return self.specification.identifier


class ScanState(object):
  """Class that implements a scan state."""

  # The state definitions.
  _SCAN_STATE_START = 1
  _SCAN_STATE_SCANNING = 2
  _SCAN_STATE_STOP = 3

  def __init__(self, scan_tree_node, total_data_size=None):
    """Initializes the scan state.

    Args:
      scan_tree_node: the corresponding scan tree node or None.
      total_data_size: optional value to indicate the total data size.
                       The default is None.
    """
    super(ScanState, self).__init__()
    self._matches = []
    self.remaining_data = None
    self.remaining_data_size = 0
    self.scan_tree_node = scan_tree_node
    self.state = self._SCAN_STATE_START
    self.total_data_offset = 0
    self.total_data_size = total_data_size

  def AddMatch(self, total_data_offset, pattern):
    """Adds a result to the state to scanning.

    Args:
      total_data_offset: the offset of the resulting match relative
                         to the start total data scanned.
      pattern: the pattern matched.

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if (self.state != self._SCAN_STATE_START and
        self.state != self._SCAN_STATE_SCANNING):
      raise RuntimeError(u'Unsupported scan state.')

    self._matches.append(_ScanMatch(total_data_offset, pattern))

  def GetMatches(self):
    """Retrieves a list containing the results.

    Returns:
      A list of scan matches (instances of _ScanMatch).

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if self.state != self._SCAN_STATE_STOP:
      raise RuntimeError(u'Unsupported scan state.')

    return self._matches

  def Reset(self, scan_tree_node):
    """Resets the state to start.

       This function will clear the remaining data.

    Args:
      scan_tree_node: the corresponding scan tree node or None.

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if self.state != self._SCAN_STATE_STOP:
      raise RuntimeError(u'Unsupported scan state.')

    self.remaining_data = None
    self.remaining_data_size = 0
    self.scan_tree_node = scan_tree_node
    self.state = self._SCAN_STATE_START

  def Scanning(self, scan_tree_node, total_data_offset):
    """Sets the state to scanning.

    Args:
      scan_tree_node: the active scan tree node.
      total_data_offset: the offset of the resulting match relative
                         to the start of the total data scanned.

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if (self.state != self._SCAN_STATE_START and
        self.state != self._SCAN_STATE_SCANNING):
      raise RuntimeError(u'Unsupported scan state.')

    self.scan_tree_node = scan_tree_node
    self.state = self._SCAN_STATE_SCANNING
    self.total_data_offset = total_data_offset

  def Stop(self):
    """Sets the state to stop.

    Raises:
      RuntimeError: when a unsupported state is encountered.
    """
    if (self.state != self._SCAN_STATE_START and
        self.state != self._SCAN_STATE_SCANNING):
      raise RuntimeError(u'Unsupported scan state.')

    self.scan_tree_node = None
    self.state = self._SCAN_STATE_STOP


class ScanTreeScannerBase(object):
  """Class that implements a scan tree-based scanner base."""

  def __init__(self, specification_store):
    """Initializes the scanner.

    Args:
      specification_store: the specification store (instance of
                           SpecificationStore) that contains the format
                           specifications.
    """
    super(ScanTreeScannerBase, self).__init__()
    self._scan_tree = None
    self._specification_store = specification_store

  def _ScanBufferScanState(
      self, scan_tree_object, scan_state, data, data_size, total_data_offset,
      total_data_size=None):
    """Scans a buffer using the scan tree.

    This function implements a Boyer–Moore–Horspool equivalent approach
    in combination with the scan tree.

    Args:
      scan_tree_object: the scan tree (instance of ScanTree).
      scan_state: the scan state (instance of ScanState).
      data: a buffer containing raw data.
      data_size: the size of the raw data in the buffer.
      total_data_offset: the offset of the data relative to the start of
                         the total data scanned.
      total_data_size: optional value to indicate the total data size.
                       The default is None.

    Raises:
      RuntimeError: if the total data offset, total data size or the last
                    pattern offset value is out of bounds
    """
    if total_data_size is not None and total_data_size < 0:
      raise RuntimeError(u'Invalid total data size, value out of bounds.')

    if total_data_offset < 0 or (
      total_data_size is not None and total_data_offset >= total_data_size):
      raise RuntimeError(u'Invalid total data offset, value out of bounds.')

    data_offset = 0
    scan_tree_node = scan_state.scan_tree_node

    if scan_state.remaining_data:
      # str.join() should be more efficient then concatenation by +.
      data = ''.join([scan_state.remaining_data, data])
      data_size += scan_state.remaining_data_size

      scan_state.remaining_data = None
      scan_state.remaining_data_size = 0

    if (total_data_size is not None and
        total_data_offset + data_size >= total_data_size):
      match_on_boundary = True
    else:
      match_on_boundary = False

    while data_offset < data_size:
      if (not match_on_boundary and
          data_offset + scan_tree_object.largest_length >= data_size):
        break

      found_match = False
      scan_done = False

      while not scan_done:
        scan_object = scan_tree_node.CompareByteValue(
            data, data_offset, data_size, total_data_offset,
            total_data_size=total_data_size)

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

            logging.debug(
                u'Signature match at data offset: 0x{0:08x}.'.format(
                    data_offset))

            scan_state.AddMatch(total_data_offset + data_offset, scan_object)

      if found_match:
        skip_value = len(scan_object.signature.expression)
        scan_tree_node = scan_tree_object.root_node
      else:
        last_pattern_offset = (
            scan_tree_object.skip_table.skip_pattern_length - 1)

        if data_offset + last_pattern_offset >= data_size:
          raise RuntimeError(
              u'Invalid last pattern offset, value out of bounds.')
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

    scan_state.Scanning(scan_tree_node, total_data_offset + data_offset)

  def _ScanBufferScanStateFinal(self, scan_tree_object, scan_state):
    """Scans the remaining data in the scan state using the scan tree.

    Args:
      scan_tree_object: the scan tree (instance of ScanTree).
      scan_state: the scan state (instance of ScanState).
    """
    if scan_state.remaining_data:
      data = scan_state.remaining_data
      data_size = scan_state.remaining_data_size

      scan_state.remaining_data = None
      scan_state.remaining_data_size = 0

      # Setting the total data size will make boundary matches are returned
      # in this scanning pass.
      total_data_size = scan_state.total_data_size
      if total_data_size is None:
        total_data_size = scan_state.total_data_offset + data_size

      self._ScanBufferScanState(
          scan_tree_object, scan_state, data, data_size,
          scan_state.total_data_offset, total_data_size=total_data_size)

    scan_state.Stop()

  def GetScanResults(self, scan_state):
    """Retrieves the scan results.

    Args:
      scan_state: the scan state (instance of ScanState).

    Return:
      A list of scan results (instances of _ScanResult).
    """
    scan_results = {}

    for scan_match in scan_state.GetMatches():
      specification = scan_match.specification
      identifier = specification.identifier

      logging.debug(
          u'Scan match at offset: 0x{0:08x} specification: {1:s}'.format(
              scan_match.total_data_offset, identifier))

      if identifier not in scan_results:
        scan_results[identifier] = _ScanResult(specification)

      scan_results[identifier].scan_matches.append(scan_match)

    return scan_results.values()


class Scanner(ScanTreeScannerBase):
  """Class that implements a scan tree-based scanner."""

  _READ_BUFFER_SIZE = 512

  def __init__(self, specification_store):
    """Initializes the scanner.

    Args:
      specification_store: the specification store (instance of
                           SpecificationStore) that contains the format
                           specifications.
    """
    super(Scanner, self).__init__(specification_store)

  def ScanBuffer(self, scan_state, data, data_size):
    """Scans a buffer.

    Args:
      scan_state: the scan state (instance of ScanState).
      data: a buffer containing raw data.
      data_size: the size of the raw data in the buffer.
    """
    self._ScanBufferScanState(
        self._scan_tree, scan_state, data, data_size,
         scan_state.total_data_offset,
        total_data_size=scan_state.total_data_size)

  def ScanFileObject(self, file_object):
    """Scans a file-like object.

    Args:
      file_object: a file-like object.

    Returns:
      A list of scan results (instances of ScanResult).
    """
    file_offset = 0

    if hasattr(file_object, 'get_size'):
      file_size = file_object.get_size()
    else:
      file_object.seek(0, os.SEEK_END)
      file_size = file_object.tell()

    scan_state = self.StartScan(total_data_size=file_size)

    file_object.seek(file_offset, os.SEEK_SET)

    while file_offset < file_size:
      data = file_object.read(self._READ_BUFFER_SIZE)
      data_size = len(data)

      if data_size == 0:
        break

      self._ScanBufferScanState(
          self._scan_tree, scan_state, data, data_size, file_offset,
          total_data_size=file_size)

      file_offset += data_size

    self.StopScan(scan_state)

    return self.GetScanResults(scan_state)

  def StartScan(self, total_data_size=None):
    """Starts a scan.

       The function sets up the scanning related structures if necessary.

    Args:
      total_data_size: optional value to indicate the total data size.
                       The default is None.
    Returns:
      A scan state (instance of ScanState).

    Raises:
      RuntimeError: when total data size is invalid.
    """
    if total_data_size is not None and total_data_size < 0:
      raise RuntimeError(u'Invalid total data size.')

    if self._scan_tree is None:
      self._scan_tree = scan_tree.ScanTree(
          self._specification_store, None)

    return ScanState(self._scan_tree.root_node, total_data_size=total_data_size)

  def StopScan(self, scan_state):
    """Stops a scan.

    Args:
      scan_state: the scan state (instance of ScanState).
    """
    self._ScanBufferScanStateFinal(self._scan_tree, scan_state)


class OffsetBoundScanner(ScanTreeScannerBase):
  """Class that implements an offset-bound scan tree-based scanner."""

  _READ_BUFFER_SIZE = 512

  def __init__(self, specification_store):
    """Initializes the scanner.

    Args:
      specification_store: the specification store (instance of
                           SpecificationStore) that contains the format
                           specifications.
    """
    super(OffsetBoundScanner, self).__init__(specification_store)
    self._footer_scan_tree = None
    self._footer_spanning_range = None
    self._header_scan_tree = None
    self._header_spanning_range = None

  def _GetFooterRange(self, total_data_size):
    """Retrieves the read buffer aligned footer range.

    Args:
      total_data_size: optional value to indicate the total data size.
                       The default is None.
    Returns:
      A range (instance of Range).
    """
    # The actual footer range is in reverse since the spanning footer range
    # is based on positive offsets, where 0 is the end of file.
    if self._footer_spanning_range.end_offset < total_data_size:
      footer_range_start_offset = (
          total_data_size - self._footer_spanning_range.end_offset)
    else:
      footer_range_start_offset = 0

    # Calculate the lower bound modulus of the footer range start offset
    # in increments of the read buffer size.
    footer_range_start_offset /= self._READ_BUFFER_SIZE
    footer_range_start_offset *= self._READ_BUFFER_SIZE

    # Calculate the upper bound modulus of the footer range size
    # in increments of the read buffer size.
    footer_range_size = self._footer_spanning_range.size
    remainder = footer_range_size % self._READ_BUFFER_SIZE
    footer_range_size /= self._READ_BUFFER_SIZE

    if remainder > 0:
      footer_range_size += 1

    footer_range_size *= self._READ_BUFFER_SIZE

    return range_list.Range(footer_range_start_offset, footer_range_size)

  def _GetHeaderRange(self):
    """Retrieves the read buffer aligned header range.

    Returns:
      A range (instance of Range).
    """
    # Calculate the lower bound modulus of the header range start offset
    # in increments of the read buffer size.
    header_range_start_offset = self._header_spanning_range.start_offset
    header_range_start_offset /= self._READ_BUFFER_SIZE
    header_range_start_offset *= self._READ_BUFFER_SIZE

    # Calculate the upper bound modulus of the header range size
    # in increments of the read buffer size.
    header_range_size = self._header_spanning_range.size
    remainder = header_range_size % self._READ_BUFFER_SIZE
    header_range_size /= self._READ_BUFFER_SIZE

    if remainder > 0:
      header_range_size += 1

    header_range_size *= self._READ_BUFFER_SIZE

    return range_list.Range(header_range_start_offset, header_range_size)

  def _ScanBufferScanState(
      self, scan_tree_object, scan_state, data, data_size, total_data_offset,
      total_data_size=None):
    """Scans a buffer using the scan tree.

    This function implements a Boyer–Moore–Horspool equivalent approach
    in combination with the scan tree.

    Args:
      scan_tree_object: the scan tree (instance of ScanTree).
      scan_state: the scan state (instance of ScanState).
      data: a buffer containing raw data.
      data_size: the size of the raw data in the buffer.
      total_data_offset: the offset of the data relative to the start of
                         the total data scanned.
      total_data_size: optional value to indicate the total data size.
                       The default is None.
    """
    scan_done = False
    scan_tree_node = scan_tree_object.root_node

    while not scan_done:
      data_offset = 0

      scan_object = scan_tree_node.CompareByteValue(
          data, data_offset, data_size, total_data_offset,
          total_data_size=total_data_size)

      if isinstance(scan_object, scan_tree.ScanTreeNode):
        scan_tree_node = scan_object
      else:
        scan_done = True

    if isinstance(scan_object, patterns.Pattern):
      pattern_length = len(scan_object.signature.expression)
      pattern_start_offset = scan_object.signature.offset
      pattern_end_offset = pattern_start_offset + pattern_length

      if cmp(scan_object.signature.expression,
             data[pattern_start_offset:pattern_end_offset]) == 0:
        scan_state.AddMatch(
            total_data_offset + scan_object.signature.offset, scan_object)

        logging.debug(
            u'Signature match at data offset: 0x{0:08x}.'.format(data_offset))

  # TODO: implement.
  # def ScanBuffer(self, scan_state, data, data_size):
  #   """Scans a buffer.

  #   Args:
  #     scan_state: the scan state (instance of ScanState).
  #     data: a buffer containing raw data.
  #     data_size: the size of the raw data in the buffer.
  #   """
  #   # TODO: fix footer scanning logic.
  #   # need to know the file size here for the footers.

  #   # TODO: check for clashing ranges?

  #   header_range = self._GetHeaderRange()
  #   footer_range = self._GetFooterRange(scan_state.total_data_size)

  #   if self._scan_tree == self._header_scan_tree:
  #     if (scan_state.total_data_offset >= header_range.start_offset and
  #         scan_state.total_data_offset < header_range.end_offset):
  #       self._ScanBufferScanState(
  #           self._scan_tree, scan_state, data, data_size,
  #           scan_state.total_data_offset,
  #           total_data_size=scan_state.total_data_size)

  #     elif scan_state.total_data_offset > header_range.end_offset:
  #       # TODO: implement.
  #       pass

  #   if self._scan_tree == self._footer_scan_tree:
  #     if (scan_state.total_data_offset >= footer_range.start_offset and
  #           scan_state.total_data_offset < footer_range.end_offset):
  #       self._ScanBufferScanState(
  #           self._scan_tree, scan_state, data, data_size,
  #           scan_state.total_data_offset,
  #           total_data_size=scan_state.total_data_size)

  def ScanFileObject(self, file_object):
    """Scans a file-like object.

    Args:
      file_object: a file-like object.

    Returns:
      A scan state (instance of ScanState).
    """
    # TODO: add support for fixed size block-based reads.

    if hasattr(file_object, 'get_size'):
      file_size = file_object.get_size()
    else:
      file_object.seek(0, os.SEEK_END)
      file_size = file_object.tell()

    file_offset = 0
    scan_state = self.StartScan(total_data_size=file_size)

    if self._header_scan_tree.root_node is not None:
      header_range = self._GetHeaderRange()

      # TODO: optimize the read by supporting fixed size block-based reads.
      # if file_offset < header_range.start_offset:
      #   file_offset = header_range.start_offset

      file_object.seek(file_offset, os.SEEK_SET)

      # TODO: optimize the read by supporting fixed size block-based reads.
      # data = file_object.read(header_range.size)
      data = file_object.read(header_range.end_offset)
      data_size = len(data)

      if data_size > 0:
        self._ScanBufferScanState(
            self._scan_tree, scan_state, data, data_size, file_offset,
            total_data_size=file_size)

      file_offset += data_size

      if self._footer_scan_tree.root_node is not None:
        self.StopScan(scan_state)

        self._scan_tree = self._footer_scan_tree
        scan_state.Reset(self._scan_tree.root_node)

    if self._footer_scan_tree.root_node is not None:
      footer_range = self._GetFooterRange(file_size)

      # Note that the offset in the footer scan tree start with 0. Make sure
      # the data offset of the data being scanned is aligned with the offset
      # in the scan tree.
      if footer_range.start_offset < self._footer_spanning_range.end_offset:
        data_offset = (
            self._footer_spanning_range.end_offset - footer_range.start_offset)
      else:
        data_offset = 0

      if file_offset < footer_range.start_offset:
        file_offset = footer_range.start_offset

      file_object.seek(file_offset, os.SEEK_SET)

      data = file_object.read(self._READ_BUFFER_SIZE)
      data_size = len(data)

      if data_size > 0:
        self._ScanBufferScanState(
            self._scan_tree, scan_state, data[data_offset:],
            data_size - data_offset, file_offset + data_offset,
            total_data_size=file_size)

      file_offset += data_size

    self.StopScan(scan_state)

    return self.GetScanResults(scan_state)

  def StartScan(self, total_data_size=None):
    """Starts a scan.

       The function sets up the scanning related structures if necessary.

    Args:
      total_data_size: optional value to indicate the total data size.
                       The default is None.
    Returns:
      A list of scan results (instances of ScanResult).

    Raises:
      RuntimeError: when total data size is invalid.
    """
    if total_data_size is None or total_data_size < 0:
      raise RuntimeError(u'Invalid total data size.')

    if self._header_scan_tree is None:
      self._header_scan_tree = scan_tree.ScanTree(
          self._specification_store, True,
          offset_mode=scan_tree.ScanTree.OFFSET_MODE_POSITIVE)

    if self._header_spanning_range is None:
      spanning_range = self._header_scan_tree.range_list.GetSpanningRange()
      self._header_spanning_range = spanning_range

    if self._footer_scan_tree is None:
      self._footer_scan_tree = scan_tree.ScanTree(
          self._specification_store, True,
          offset_mode=scan_tree.ScanTree.OFFSET_MODE_NEGATIVE)

    if self._footer_spanning_range is None:
      spanning_range = self._footer_scan_tree.range_list.GetSpanningRange()
      self._footer_spanning_range = spanning_range

    if self._header_scan_tree.root_node is not None:
      self._scan_tree = self._header_scan_tree
    elif self._footer_scan_tree.root_node is not None:
      self._scan_tree = self._footer_scan_tree
    else:
      self._scan_tree = None

    if self._scan_tree is not None:
      root_node = self._scan_tree.root_node
    else:
      root_node = None

    return ScanState(root_node, total_data_size=total_data_size)

  def StopScan(self, scan_state):
    """Stops a scan.

    Args:
      scan_state: the scan state (instance of ScanState).
    """
    self._ScanBufferScanStateFinal(self._scan_tree, scan_state)
    self._scan_tree = None
