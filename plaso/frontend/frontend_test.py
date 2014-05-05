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
"""Tests for the front-end object."""

import os
import unittest

from dfvfs.lib import definitions

from plaso.frontend import frontend

class TestConfig(object):
  """Class that defines the test config object."""


class FrontendTests(unittest.TestCase):
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

  def _TestScanSourceDirectory(self, test_file):
    """Tests the ScanSource function on a directory.

    Args:
      test_file: the path of the test file.
    """
    options = TestConfig()
    options.source = test_file

    path_spec = self._test_front_end.ScanSource(options, 'source')
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.location, os.path.abspath(options.source))
    self.assertEquals(
        path_spec.type_indicator, definitions.TYPE_INDICATOR_OS)
    self.assertEquals(options.image_offset_bytes, None)

  def _TestScanSourceImage(self, test_file):
    """Tests the ScanSource function on the test image.

    Args:
      test_file: the path of the test file.
    """
    options = TestConfig()
    options.source = test_file

    path_spec = self._test_front_end.ScanSource(options, 'source')
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(options.image_offset_bytes, 0)

  def _TestScanSourcePartitionedImage(self, test_file):
    """Tests the ScanSource function on the partitioned test image.

    Args:
      test_file: the path of the test file.
    """
    options = TestConfig()
    options.source = test_file
    options.image_offset_bytes = 0x0002c000

    path_spec = self._test_front_end.ScanSource(options, 'source')
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(options.image_offset_bytes, 180224)

    options = TestConfig()
    options.source = test_file
    options.image_offset = 352
    options.bytes_per_sector = 512

    path_spec = self._test_front_end.ScanSource(options, 'source')
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(options.image_offset_bytes, 180224)

    options = TestConfig()
    options.source = test_file
    options.partition_number = 1

    path_spec = self._test_front_end.ScanSource(options, 'source')
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(options.image_offset_bytes, 180224)

  def _TestScanSourceVssImage(self, test_file):
    """Tests the ScanSource function on the VSS test image.

    Args:
      test_file: the path of the test file.
    """
    options = TestConfig()
    options.source = test_file
    options.vss_stores = '1,2'

    path_spec = self._test_front_end.ScanSource(options, 'source')
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(options.image_offset_bytes, 0)
    self.assertEquals(options.vss_stores, [1, 2])

    options = TestConfig()
    options.source = test_file
    options.vss_stores = '1'

    path_spec = self._test_front_end.ScanSource(options, 'source')
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, definitions.TYPE_INDICATOR_TSK)
    self.assertEquals(options.image_offset_bytes, 0)
    self.assertEquals(options.vss_stores, [1])

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._test_front_end = frontend.Frontend()

  def testScanSource(self):
    """Tests the ScanSource function."""
    test_file = self._GetTestFilePath(['tsk_volume_system.raw'])
    self._TestScanSourcePartitionedImage(test_file)

    test_file = self._GetTestFilePath(['image-split.E01'])
    self._TestScanSourcePartitionedImage(test_file)

    test_file = self._GetTestFilePath(['image.E01'])
    self._TestScanSourceImage(test_file)

    test_file = self._GetTestFilePath(['image.qcow2'])
    self._TestScanSourceImage(test_file)

    test_file = self._GetTestFilePath(['vsstest.qcow2'])
    self._TestScanSourceVssImage(test_file)

    test_file = self._GetTestFilePath(['text_parser'])
    self._TestScanSourceDirectory(test_file)

    test_file = self._GetTestFilePath(['image.vhd'])
    self._TestScanSourceImage(test_file)

    test_file = self._GetTestFilePath(['image.vmdk'])
    self._TestScanSourceImage(test_file)


if __name__ == '__main__':
  unittest.main()
