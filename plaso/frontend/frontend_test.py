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

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.frontend import frontend
from plaso.frontend import test_lib
from plaso.lib import errors
from plaso.lib import storage


class ExtractionFrontendTests(test_lib.FrontendTestCase):
  """Tests for the extraction front-end object."""

  def _TestScanSourceDirectory(self, test_file):
    """Tests the ScanSource function on a directory.

    Args:
      test_file: the path of the test file.
    """
    test_front_end = frontend.ExtractionFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()
    options.source = test_file

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(path_spec.location, os.path.abspath(test_file))
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_OS)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, None)

  def _TestScanSourceImage(self, test_file):
    """Tests the ScanSource function on the test image.

    Args:
      test_file: the path of the test file.
    """
    test_front_end = frontend.ExtractionFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()
    options.source = test_file

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, 0)

  def _TestScanSourcePartitionedImage(self, test_file):
    """Tests the ScanSource function on the partitioned test image.

    Args:
      test_file: the path of the test file.
    """
    test_front_end = frontend.ExtractionFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()
    options.source = test_file
    options.image_offset_bytes = 0x0002c000

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, 180224)

    options = frontend.Options()
    options.source = test_file
    options.image_offset = 352
    options.bytes_per_sector = 512

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, 180224)

    options = frontend.Options()
    options.source = test_file
    options.partition_number = 2

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, 180224)

  def _TestScanSourceVssImage(self, test_file):
    """Tests the ScanSource function on the VSS test image.

    Args:
      test_file: the path of the test file.
    """
    test_front_end = frontend.ExtractionFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()
    options.source = test_file
    options.vss_stores = '1,2'

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, 0)
    self.assertEquals(test_front_end._vss_stores, [1, 2])

    options = frontend.Options()
    options.source = test_file
    options.vss_stores = '1'

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, 0)
    self.assertEquals(test_front_end._vss_stores, [1])

    options = frontend.Options()
    options.source = test_file
    options.vss_stores = 'all'

    test_front_end.ParseOptions(options)

    test_front_end.ScanSource(options)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEquals(path_spec, None)
    self.assertEquals(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    # pylint: disable=protected-access
    self.assertEquals(test_front_end._partition_offset, 0)
    self.assertEquals(test_front_end._vss_stores, [1, 2])

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._input_reader = frontend.StdinFrontendInputReader()
    self._output_writer = frontend.StdoutFrontendOutputWriter()

  def testParseOptions(self):
    """Tests the parse options function."""
    test_front_end = frontend.ExtractionFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()

    with self.assertRaises(errors.BadConfigOption):
      test_front_end.ParseOptions(options)

    options.source = self._GetTestFilePath([u'ímynd.dd'])

    test_front_end.ParseOptions(options)

  def testScanSource(self):
    """Tests the ScanSource function."""
    test_file = self._GetTestFilePath([u'tsk_volume_system.raw'])
    self._TestScanSourcePartitionedImage(test_file)

    test_file = self._GetTestFilePath([u'image-split.E01'])
    self._TestScanSourcePartitionedImage(test_file)

    test_file = self._GetTestFilePath([u'image.E01'])
    self._TestScanSourceImage(test_file)

    test_file = self._GetTestFilePath([u'image.qcow2'])
    self._TestScanSourceImage(test_file)

    test_file = self._GetTestFilePath([u'vsstest.qcow2'])
    self._TestScanSourceVssImage(test_file)

    test_file = self._GetTestFilePath([u'text_parser'])
    self._TestScanSourceDirectory(test_file)

    test_file = self._GetTestFilePath([u'image.vhd'])
    self._TestScanSourceImage(test_file)

    test_file = self._GetTestFilePath([u'image.vmdk'])
    self._TestScanSourceImage(test_file)

    with self.assertRaises(errors.SourceScannerError):
      test_file = self._GetTestFilePath(['nosuchfile.raw'])
      self._TestScanSourceImage(test_file)


class AnalysisFrontendTests(test_lib.FrontendTestCase):
  """Tests for the analysis front-end object."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._input_reader = frontend.StdinFrontendInputReader()
    self._output_writer = frontend.StdoutFrontendOutputWriter()

  def testOpenStorageFile(self):
    """Tests the open storage file function."""
    test_front_end = frontend.AnalysisFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()
    options.storage_file = self._GetTestFilePath([u'psort_test.out'])

    test_front_end.ParseOptions(options)
    storage_file = test_front_end.OpenStorageFile()

    self.assertIsInstance(storage_file, storage.StorageFile)

    storage_file.Close()

  def testParseOptions(self):
    """Tests the parse options function."""
    test_front_end = frontend.AnalysisFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()

    with self.assertRaises(errors.BadConfigOption):
      test_front_end.ParseOptions(options)

    options.storage_file = self._GetTestFilePath([u'no_such_file.out'])

    with self.assertRaises(errors.BadConfigOption):
      test_front_end.ParseOptions(options)

    options.storage_file = self._GetTestFilePath([u'psort_test.out'])

    test_front_end.ParseOptions(options)


if __name__ == '__main__':
  unittest.main()
