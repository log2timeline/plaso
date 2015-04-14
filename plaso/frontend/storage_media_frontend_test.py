#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction front-end object."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.frontend import storage_media_frontend
from plaso.frontend import test_lib
from plaso.lib import errors


class StorageMediaFrontendTests(test_lib.FrontendTestCase):
  """Tests for the storage media front-end object."""

  def _TestScanSourceDirectory(self, source_path):
    """Tests the ScanSource function on a directory.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    test_front_end.ScanSource(source_path)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEqual(path_spec, None)
    self.assertEqual(path_spec.location, os.path.abspath(source_path))
    self.assertEqual(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_OS)
    self.assertEqual(test_front_end.partition_offset, None)

  def _TestScanSourceImage(self, source_path):
    """Tests the ScanSource function on the test image.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    test_front_end.ScanSource(source_path)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEqual(path_spec, None)
    self.assertEqual(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEqual(test_front_end.partition_offset, 0)

  def _TestScanSourcePartitionedImage(self, source_path):
    """Tests the ScanSource function on the partitioned test image.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    test_front_end.ScanSource(source_path, partition_offset=0x0002c000)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEqual(path_spec, None)
    self.assertEqual(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEqual(test_front_end.partition_offset, 180224)

    test_front_end.ScanSource(source_path, partition_number=2)
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEqual(path_spec, None)
    self.assertEqual(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEqual(test_front_end.partition_offset, 180224)

  def _TestScanSourceVssImage(self, source_path):
    """Tests the ScanSource function on the VSS test image.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    test_front_end.ScanSource(source_path, enable_vss=True, vss_stores=[1, 2])
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEqual(path_spec, None)
    self.assertEqual(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEqual(test_front_end.partition_offset, 0)
    self.assertEqual(test_front_end.vss_stores, [1, 2])

    test_front_end.ScanSource(source_path, enable_vss=True, vss_stores=[1])
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEqual(path_spec, None)
    self.assertEqual(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEqual(test_front_end.partition_offset, 0)
    self.assertEqual(test_front_end.vss_stores, [1])

    test_front_end.ScanSource(source_path, enable_vss=True, vss_stores=[u'all'])
    path_spec = test_front_end.GetSourcePathSpec()
    self.assertNotEqual(path_spec, None)
    self.assertEqual(
        path_spec.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)
    self.assertEqual(test_front_end.partition_offset, 0)
    self.assertEqual(test_front_end.vss_stores, [1, 2])

  def testScanSource(self):
    """Tests the ScanSource function."""
    source_path = self._GetTestFilePath([u'tsk_volume_system.raw'])
    self._TestScanSourcePartitionedImage(source_path)

    source_path = self._GetTestFilePath([u'image-split.E01'])
    self._TestScanSourcePartitionedImage(source_path)

    source_path = self._GetTestFilePath([u'image.E01'])
    self._TestScanSourceImage(source_path)

    source_path = self._GetTestFilePath([u'image.qcow2'])
    self._TestScanSourceImage(source_path)

    source_path = self._GetTestFilePath([u'vsstest.qcow2'])
    self._TestScanSourceVssImage(source_path)

    source_path = self._GetTestFilePath([u'text_parser'])
    self._TestScanSourceDirectory(source_path)

    source_path = self._GetTestFilePath([u'image.vhd'])
    self._TestScanSourceImage(source_path)

    source_path = self._GetTestFilePath([u'image.vmdk'])
    self._TestScanSourceImage(source_path)

    with self.assertRaises(errors.SourceScannerError):
      source_path = self._GetTestFilePath([u'nosuchfile.raw'])
      self._TestScanSourceImage(source_path)


if __name__ == '__main__':
  unittest.main()
