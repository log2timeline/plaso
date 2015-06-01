#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage media front-end object."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.frontend import storage_media_frontend
from plaso.frontend import test_lib
from plaso.lib import errors


class StorageMediaFrontendTests(test_lib.FrontendTestCase):
  """Tests for the storage media front-end object."""

  def _GetTestScanNode(self, scan_context):
    """Retrieves the scan node for testing.

    Retrieves the first scan node, from the root upwards, with more or less
    than 1 sub node.

    Args:
      scan_context: scan context (instance of dfvfs.ScanContext).

    Returns:
      A scan node (instance of dfvfs.ScanNode).
    """
    scan_node = scan_context.GetRootScanNode()
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    return scan_node

  def _TestScanSourceDirectory(self, source_path):
    """Tests the ScanSource function on a directory.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    scan_context = test_front_end.ScanSource(source_path)
    self.assertNotEqual(scan_context, None)

    scan_node = scan_context.GetRootScanNode()
    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_OS)

    path_spec = scan_node.path_spec
    self.assertEqual(path_spec.location, os.path.abspath(source_path))

  def _TestScanSourceImage(self, source_path):
    """Tests the ScanSource function on an image containing a single partition.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    scan_context = test_front_end.ScanSource(source_path)
    self.assertNotEqual(scan_context, None)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)

  def _TestScanSourcePartitionedImage(self, source_path):
    """Tests the ScanSource function on an image containing multiple partitions.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    scan_context = test_front_end.ScanSource(source_path)
    self.assertNotEqual(scan_context, None)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION)
    self.assertEqual(len(scan_node.sub_nodes), 7)

    for scan_node in scan_node.sub_nodes:
      if getattr(scan_node.path_spec, u'location', None) == u'/p2':
        break

    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION)
    self.assertEqual(len(scan_node.sub_nodes), 1)

    path_spec = scan_node.path_spec
    self.assertEqual(path_spec.start_offset, 180224)

    scan_node = scan_node.sub_nodes[0]
    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)

  def _TestScanSourceVssImage(self, source_path):
    """Tests the ScanSource function on a VSS storage media image.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_front_end = storage_media_frontend.StorageMediaFrontend()

    scan_context = test_front_end.ScanSource(source_path)
    self.assertNotEqual(scan_context, None)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW)
    self.assertEqual(len(scan_node.sub_nodes), 3)

    for scan_node in scan_node.sub_nodes:
      if getattr(scan_node.path_spec, u'location', None) == u'/':
        break

    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)

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
