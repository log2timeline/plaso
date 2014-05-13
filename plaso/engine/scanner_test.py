#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the file system scanner object."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.engine import engine
from plaso.engine import scanner


class UserInputException(Exception):
  """Class that defines an user input exception."""


class TestFileSystemScanner(scanner.FileSystemScanner):
  """Test file system scanner that raises UserInputException."""

  def _GetPartionIdentifierFromUser(self, volume_system, volume_identifiers):
    """Asks the user to provide the partitioned volume identifier.

    Args:
      volume_system: The volume system (instance of dfvfs.TSKVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.
    """
    raise UserInputException(u'_GetPartionIdentifierFromUser')

  def _GetVShadowIdentifiersFromUser(self, volume_system, volume_identifiers):
    """Asks the user to provide the VSS volume identifiers.

    Args:
      volume_system: The volume system (instance of dfvfs.VShadowVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.
    """
    self.vss_stores = [1, 2]
    return self.vss_stores


class FileSystemScannerTest(unittest.TestCase):
  """Tests for the file system scanner."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

  def _TestScanImage(self, test_file):
    """Tests file systems scanning on the test image.

    Args:
      test_file: the path of the test file.
    """
    test_scanner = TestFileSystemScanner(
        self._input_reader, self._output_writer)

    path_spec = test_scanner.Scan(test_file)
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(test_scanner.partition_offset, 0)

  def _TestScanPartionedImage(self, test_file):
    """Tests file systems scanning on the partitioned test image.

    Args:
      test_file: the path of the test file.
    """
    test_scanner = TestFileSystemScanner(
        self._input_reader, self._output_writer)
    with self.assertRaises(UserInputException):
      _ = test_scanner.Scan(test_file)

    test_scanner = TestFileSystemScanner(
        self._input_reader, self._output_writer)
    test_scanner.SetPartitionOffset(0x0002c000)

    path_spec = test_scanner.Scan(test_file)
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(test_scanner.partition_offset, 180224)

    test_scanner = TestFileSystemScanner(
        self._input_reader, self._output_writer)
    test_scanner.SetPartitionOffset(0x00030000)
    with self.assertRaises(UserInputException):
      _ = test_scanner.Scan(test_file)

    test_scanner = TestFileSystemScanner(
        self._input_reader, self._output_writer)
    test_scanner.SetPartitionNumber(1)

    path_spec = test_scanner.Scan(test_file)
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(test_scanner.partition_offset, 180224)

    test_scanner = TestFileSystemScanner(
        self._input_reader, self._output_writer)
    test_scanner.SetPartitionNumber(7)
    with self.assertRaises(UserInputException):
      _ = test_scanner.Scan(test_file)

  def _TestScanVssImage(self, test_file):
    """Tests file systems scanning on the VSS test image.

    Args:
      test_file: the path of the test file.
    """
    test_scanner = TestFileSystemScanner(
        self._input_reader, self._output_writer)

    path_spec = test_scanner.Scan(test_file)
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(test_scanner.partition_offset, 0)
    self.assertEquals(test_scanner.vss_stores, [1, 2])

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._input_reader = engine.StdinEngineInputReader()
    self._output_writer = engine.StdoutEngineOutputWriter()

  def testScan(self):
    """Tests file systems scanning."""
    test_file = self._GetTestFilePath(['tsk_volume_system.raw'])
    self._TestScanPartionedImage(test_file)

    test_file = self._GetTestFilePath(['image.E01'])
    self._TestScanImage(test_file)

    test_file = self._GetTestFilePath(['image.qcow2'])
    self._TestScanImage(test_file)

    test_file = self._GetTestFilePath(['vsstest.qcow2'])
    self._TestScanVssImage(test_file)

    test_file = self._GetTestFilePath(['image-split.E01'])
    self._TestScanPartionedImage(test_file)

    test_file = self._GetTestFilePath(['image.vhd'])
    self._TestScanImage(test_file)

    test_file = self._GetTestFilePath(['image.vmdk'])
    self._TestScanImage(test_file)


if __name__ == '__main__':
  unittest.main()
