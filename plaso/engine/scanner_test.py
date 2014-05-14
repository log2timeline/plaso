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

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.engine import scanner
from plaso.engine import test_lib


class FileSystemScannerTest(test_lib.EngineTestCase):
  """Tests for the file system scanner."""

  def _TestScanForFileSystem(self, source_path_spec, expected_type_indicator):
    """Tests the scan for file system function.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).
      expected_type_indicator: the expected result path specification type
                               indicator.
    """
    path_spec = self._test_scanner.ScanForFileSystem(source_path_spec)
    self.assertNotEquals(path_spec, None)
    self.assertEquals(path_spec.type_indicator, expected_type_indicator)

  def _TestScanForVolumeSystem(self, source_path_spec, expected_type_indicator):
    """Tests the scan for volume system function.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).
      expected_type_indicator: the expected result path specification type
                               indicator.
    """
    path_spec = self._test_scanner.ScanForVolumeSystem(source_path_spec)
    self.assertNotEquals(path_spec, None)
    self.assertEquals(path_spec.type_indicator, expected_type_indicator)

  def _TestScanForStorageMediaImage(
      self, source_path_spec, expected_type_indicator):
    """Tests the scan for storage media image function.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).
      expected_type_indicator: the expected result path specification type
                               indicator.
    """
    path_spec = self._test_scanner.ScanForStorageMediaImage(source_path_spec)
    self.assertNotEquals(path_spec, None)
    self.assertEquals(path_spec.type_indicator, expected_type_indicator)

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._test_scanner = scanner.FileSystemScanner()

  def testScanForFileSystem(self):
    """Tests the scan for file system function."""
    test_file = self._GetTestFilePath(['image.dd'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForFileSystem(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_TSK)

    test_file = self._GetTestFilePath(['image.E01'])
    image_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    path_spec = self._test_scanner.ScanForStorageMediaImage(image_path_spec)
    self._TestScanForFileSystem(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_TSK)

  def testScanForVolumeSystem(self):
    """Tests the scan for volume system function."""
    test_file = self._GetTestFilePath(['tsk_volume_system.raw'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForVolumeSystem(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION)

  def testScanForStorageMediaImage(self):
    """Tests the scan for storage media image function."""
    test_file = self._GetTestFilePath(['tsk_volume_system.raw'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)

    path_spec = self._test_scanner.ScanForStorageMediaImage(path_spec)
    self.assertEquals(path_spec, None)

    test_file = self._GetTestFilePath(['image.E01'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForStorageMediaImage(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_EWF)

    test_file = self._GetTestFilePath(['image-split.E01'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForStorageMediaImage(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_EWF)

    test_file = self._GetTestFilePath(['image.qcow2'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForStorageMediaImage(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_QCOW)

    test_file = self._GetTestFilePath(['vsstest.qcow2'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForStorageMediaImage(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_QCOW)

    test_file = self._GetTestFilePath(['image.vhd'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForStorageMediaImage(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_VHDI)

    test_file = self._GetTestFilePath(['image.vmdk'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    self._TestScanForStorageMediaImage(
        path_spec, dfvfs_definitions.TYPE_INDICATOR_VMDK)


if __name__ == '__main__':
  unittest.main()
