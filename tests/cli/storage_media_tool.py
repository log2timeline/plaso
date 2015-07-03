#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage media tool object."""

import argparse
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.cli import storage_media_tool
from plaso.lib import errors

from tests.cli import test_lib


class StorageMediaToolTest(test_lib.CLIToolTestCase):
  """Tests for the storage media tool object."""

  _EXPECTED_OUTPUT_CREDENTIAL_OPTIONS = u'\n'.join([
      u'usage: storage_media_tool_test.py [--credential TYPE:DATA]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --credential TYPE:DATA',
      (u'                        Define a credentials that can be used to '
       u'unlock'),
      (u'                        encrypted volumes e.g. BitLocker. The '
       u'credential is'),
      (u'                        defined as type:data e.g. '
       u'"password:BDE-test".'),
      (u'                        Supported credential types are: key_data, '
       u'password,'),
      (u'                        recovery_password, startup_key. Binary '
       u'key data is'),
      u'                        expected to be passed in BASE-16 encoding',
      (u'                        (hexadecimal). WARNING credentials passed '
       u'via command'),
      (u'                        line arguments can end up in logs, so use '
       u'this option'),
      u'                        with care.',
      u''])

  _EXPECTED_OUTPUT_FILTER_OPTIONS = u'\n'.join([
      u'usage: storage_media_tool_test.py [-f FILE_FILTER]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  -f FILE_FILTER, --file_filter FILE_FILTER, --file-filter FILE_FILTER',
      (u'                        List of files to include for targeted '
       u'collection of'),
      (u'                        files to parse, one line per file path, '
       u'setup is'),
      (u'                        /path|file - where each element can contain '
       u'either a'),
      (u'                        variable set in the preprocessing stage or '
       u'a regular'),
      u'                        expression.',
      u''])

  _EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS = u'\n'.join([
      u'usage: storage_media_tool_test.py [--partition PARTITION_NUMBER]',
      u'                                  [-o IMAGE_OFFSET]',
      u'                                  [--sector_size BYTES_PER_SECTOR]',
      u'                                  [--ob IMAGE_OFFSET_BYTES]',
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      u'  --partition PARTITION_NUMBER',
      (u'                        Choose a partition number from a disk image. '
       u'This'),
      (u'                        partition number should correspond to the '
       u'partition'),
      (u'                        number on the disk image, starting from '
       u'partition 1.'),
      u'                        All partitions can be defined as: "all".',
      u'  -o IMAGE_OFFSET, --offset IMAGE_OFFSET',
      (u'                        The offset of the volume within the storage '
       u'media'),
      (u'                        image in number of sectors. A sector is 512 '
       u'bytes in'),
      (u'                        size by default this can be overwritten with '
       u'the'),
      u'                        --sector_size option.',
      u'  --sector_size BYTES_PER_SECTOR, --sector-size BYTES_PER_SECTOR',
      (u'                        The number of bytes per sector, which is 512 '
       u'by'),
      u'                        default.',
      (u'  --ob IMAGE_OFFSET_BYTES, --offset_bytes IMAGE_OFFSET_BYTES, '
       u'--offset_bytes IMAGE_OFFSET_BYTES'),
      (u'                        The offset of the volume within the storage '
       u'media'),
      u'                        image in number of bytes.',
      u''])

  _EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS = u'\n'.join([
      (u'usage: storage_media_tool_test.py [--no_vss] '
       u'[--vss_stores VSS_STORES]'),
      u'',
      u'Test argument parser.',
      u'',
      u'optional arguments:',
      (u'  --no_vss, --no-vss    Do not scan for Volume Shadow Snapshots '
       u'(VSS). This'),
      (u'                        means that VSS information will not be '
       u'included in the'),
      u'                        extraction phase.',
      u'  --vss_stores VSS_STORES, --vss-stores VSS_STORES',
      (u'                        Define Volume Shadow Snapshots (VSS) (or '
       u'stores that'),
      (u'                        need to be processed. A range of stores can '
       u'be defined'),
      (u'                        as: "3..5". Multiple stores can be defined '
       u'as: "1,3,5"'),
      (u'                        (a list of comma separated values). Ranges '
       u'and lists'),
      (u'                        can also be combined as: "1,3..5". The '
       u'first store is'),
      u'                        1. All stores can be defined as: "all".',
      u''])

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
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.source = source_path
    test_tool.ParseOptions(options)

    scan_context = test_tool.ScanSource()
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
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.source = source_path
    test_tool.ParseOptions(options)

    scan_context = test_tool.ScanSource()
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
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.partition_number = u'all'
    options.source = source_path
    test_tool.ParseOptions(options)

    scan_context = test_tool.ScanSource()
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

  def _TestScanSourceVSSImage(self, source_path):
    """Tests the ScanSource function on a VSS storage media image.

    Args:
      source_path: the path of the source device, directory or file.
    """
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.source = source_path
    options.vss_stores = u'all'
    test_tool.ParseOptions(options)

    scan_context = test_tool.ScanSource()
    self.assertNotEqual(scan_context, None)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_QCOW)
    self.assertEqual(len(scan_node.sub_nodes), 2)

    volume_scan_node = scan_node

    scan_node = volume_scan_node.sub_nodes[0]
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_VSHADOW)
    self.assertEqual(len(scan_node.sub_nodes), 2)

    scan_node = scan_node.sub_nodes[0]
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_VSHADOW)
    # By default the file system inside a VSS volume is not scanned.
    self.assertEqual(len(scan_node.sub_nodes), 0)

    scan_node = volume_scan_node.sub_nodes[1]
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)

  def testAddCredentialOptions(self):
    """Tests the AddCredentialOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'storage_media_tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddCredentialOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_CREDENTIAL_OPTIONS)

  def testAddFilterOptions(self):
    """Tests the AddFilterOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'storage_media_tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddFilterOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_FILTER_OPTIONS)

  def testAddStorageMediaImageOptions(self):
    """Tests the AddStorageMediaImageOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'storage_media_tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddStorageMediaImageOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS)

  def testAddVSSProcessingOptions(self):
    """Tests the AddVSSProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog=u'storage_media_tool_test.py',
        description=u'Test argument parser.',
        add_help=False)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddVSSProcessingOptions(argument_parser)

    output = argument_parser.format_help()
    self.assertEqual(output, self._EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.source = self._GetTestFilePath([u'ímynd.dd'])

    test_tool.ParseOptions(options)

    # TODO: improve this test.

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
    self._TestScanSourceVSSImage(source_path)

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
