#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the storage media tool object."""

from __future__ import unicode_literals

import argparse
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import storage_media_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class StorageMediaToolTest(test_lib.CLIToolTestCase):
  """Tests for the storage media tool object."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT_CREDENTIAL_OPTIONS = '\n'.join([
      'usage: storage_media_tool_test.py [--credential TYPE:DATA]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      '  --credential TYPE:DATA',
      ('                        Define a credentials that can be used to '
       'unlock'),
      ('                        encrypted volumes e.g. BitLocker. The '
       'credential is'),
      ('                        defined as type:data e.g. '
       '"password:BDE-test".'),
      ('                        Supported credential types are: key_data, '
       'password,'),
      ('                        recovery_password, startup_key. Binary '
       'key data is'),
      '                        expected to be passed in BASE-16 encoding',
      ('                        (hexadecimal). WARNING credentials passed '
       'via command'),
      ('                        line arguments can end up in logs, so use '
       'this option'),
      '                        with care.',
      ''])

  _EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS = """\
usage: storage_media_tool_test.py [--partition PARTITION]
                                  [--partitions PARTITIONS]
                                  [--offset IMAGE_OFFSET]
                                  [--ob IMAGE_OFFSET_BYTES]
                                  [--sector_size BYTES_PER_SECTOR]

Test argument parser.

optional arguments:
  --ob IMAGE_OFFSET_BYTES, --offset_bytes IMAGE_OFFSET_BYTES, --offset_bytes IMAGE_OFFSET_BYTES
                        The offset of the volume within the storage media
                        image in number of bytes.
  --offset IMAGE_OFFSET
                        The offset of the volume within the storage media
                        image in number of sectors. A sector is 512 bytes in
                        size by default this can be overwritten with the
                        --sector_size option.
  --partition PARTITION
                        Choose a partition number from a disk image. This
                        partition number should correspond to the partition
                        number on the disk image, starting from partition 1.
                        All partitions can be defined as: "all".
  --partitions PARTITIONS
                        Define partitions that need to be processed. A range
                        of partitions can be defined as: "3..5". Multiple
                        partitions can be defined as: "1,3,5" (a list of comma
                        separated values). Ranges and lists can also be
                        combined as: "1,3..5". The first partition is 1. All
                        partitions can be defined as: "all".
  --sector_size BYTES_PER_SECTOR, --sector-size BYTES_PER_SECTOR
                        The number of bytes per sector, which is 512 by
                        default.
"""

  _EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS = '\n'.join([
      'usage: storage_media_tool_test.py [--no_vss] [--vss_only]',
      '                                  [--vss_stores VSS_STORES]',
      '',
      'Test argument parser.',
      '',
      'optional arguments:',
      ('  --no_vss, --no-vss    Do not scan for Volume Shadow Snapshots '
       '(VSS). This'),
      ('                        means that Volume Shadow Snapshots (VSS) '
       'are not'),
      '                        processed.',
      '  --vss_only, --vss-only',
      ('                        Do not process the current volume if '
       'Volume Shadow'),
      '                        Snapshots (VSS) have been selected.',
      '  --vss_stores VSS_STORES, --vss-stores VSS_STORES',
      ('                        Define Volume Shadow Snapshots (VSS) (or '
       'stores that'),
      ('                        need to be processed. A range of stores can '
       'be defined'),
      ('                        as: "3..5". Multiple stores can be defined '
       'as: "1,3,5"'),
      ('                        (a list of comma separated values). Ranges '
       'and lists'),
      ('                        can also be combined as: "1,3..5". The '
       'first store is'),
      '                        1. All stores can be defined as: "all".',
      ''])

  def _GetTestScanNode(self, scan_context):
    """Retrieves the scan node for testing.

    Retrieves the first scan node, from the root upwards, with more or less
    than 1 sub node.

    Args:
      scan_context (dfvfs.ScanContext): scan context.

    Returns:
      dfvfs.ScanNode: scan node.
    """
    scan_node = scan_context.GetRootScanNode()
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    return scan_node

  def _TestScanSourceDirectory(self, source_path):
    """Tests the ScanSource function on a directory.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.source = source_path

    test_tool._ParseStorageMediaImageOptions(options)
    test_tool._ParseVSSProcessingOptions(options)
    test_tool._ParseCredentialOptions(options)
    test_tool._ParseSourcePathOption(options)

    scan_context = test_tool.ScanSource(source_path)
    self.assertIsNotNone(scan_context)

    scan_node = scan_context.GetRootScanNode()
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_OS)

    path_spec = scan_node.path_spec
    self.assertEqual(path_spec.location, os.path.abspath(source_path))

  def _TestScanSourceImage(self, source_path):
    """Tests the ScanSource function on an image containing a single partition.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.source = source_path

    test_tool._ParseStorageMediaImageOptions(options)
    test_tool._ParseVSSProcessingOptions(options)
    test_tool._ParseCredentialOptions(options)
    test_tool._ParseSourcePathOption(options)

    scan_context = test_tool.ScanSource(source_path)
    self.assertIsNotNone(scan_context)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)

  def _TestScanSourcePartitionedImage(self, source_path):
    """Tests the ScanSource function on an image containing multiple partitions.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.partitions = 'all'
    options.source = source_path

    test_tool._ParseStorageMediaImageOptions(options)
    test_tool._ParseVSSProcessingOptions(options)
    test_tool._ParseCredentialOptions(options)
    test_tool._ParseSourcePathOption(options)

    scan_context = test_tool.ScanSource(source_path)
    self.assertIsNotNone(scan_context)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION)
    self.assertEqual(len(scan_node.sub_nodes), 7)

    for scan_node in scan_node.sub_nodes:
      if getattr(scan_node.path_spec, 'location', None) == '/p2':
        break

    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION)
    self.assertEqual(len(scan_node.sub_nodes), 1)

    path_spec = scan_node.path_spec
    self.assertEqual(path_spec.start_offset, 180224)

    scan_node = scan_node.sub_nodes[0]
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)

  def _TestScanSourceVSSImage(self, source_path):
    """Tests the ScanSource function on a VSS storage media image.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.source = source_path
    options.vss_stores = 'all'

    test_tool._ParseStorageMediaImageOptions(options)
    test_tool._ParseVSSProcessingOptions(options)
    test_tool._ParseCredentialOptions(options)
    test_tool._ParseSourcePathOption(options)

    scan_context = test_tool.ScanSource(source_path)
    self.assertIsNotNone(scan_context)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertIsNotNone(scan_node)
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

  def testFormatHumanReadableSize(self):
    """Tests the _FormatHumanReadableSize function."""
    test_tool = storage_media_tool.StorageMediaTool()

    expected_size_string = '1000 B'
    size_string = test_tool._FormatHumanReadableSize(1000)
    self.assertEqual(size_string, expected_size_string)

    expected_size_string = '1.0KiB / 1.0kB (1024 B)'
    size_string = test_tool._FormatHumanReadableSize(1024)
    self.assertEqual(size_string, expected_size_string)

    expected_size_string = '976.6KiB / 1.0MB (1000000 B)'
    size_string = test_tool._FormatHumanReadableSize(1000000)
    self.assertEqual(size_string, expected_size_string)

    expected_size_string = '1.0MiB / 1.0MB (1048576 B)'
    size_string = test_tool._FormatHumanReadableSize(1048576)
    self.assertEqual(size_string, expected_size_string)

  @shared_test_lib.skipUnlessHasTestFile(['tsk_volume_system.raw'])
  def testGetNormalizedTSKVolumeIdentifiers(self):
    """Tests the _GetNormalizedTSKVolumeIdentifiers function."""
    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, parent=os_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(tsk_partition_path_spec)

    volume_identifiers = test_tool._GetNormalizedTSKVolumeIdentifiers(
        volume_system, ['p1', 'p2'])
    self.assertEqual(volume_identifiers, [1, 2])

    with self.assertRaises(KeyError):
      test_tool._GetNormalizedTSKVolumeIdentifiers(
          volume_system, [1, 2])

    with self.assertRaises(KeyError):
      test_tool._GetNormalizedTSKVolumeIdentifiers(
          volume_system, ['p3'])

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testGetNormalizedVShadowVolumeIdentifiers(self):
    """Tests the _GetNormalizedVShadowVolumeIdentifiers function."""
    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    vss_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, parent=qcow_path_spec)

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(vss_path_spec)

    volume_identifiers = test_tool._GetNormalizedVShadowVolumeIdentifiers(
        volume_system, ['vss1', 'vss2'])
    self.assertEqual(volume_identifiers, [1, 2])

    with self.assertRaises(KeyError):
      test_tool._GetNormalizedTSKVolumeIdentifiers(
          volume_system, [1, 2])

    with self.assertRaises(KeyError):
      test_tool._GetNormalizedTSKVolumeIdentifiers(
          volume_system, ['vss3'])

  # TODO: add test for _GetTSKPartitionIdentifiers.
  # TODO: add test for _GetVSSStoreIdentifiers.

  def testParseCredentialOptions(self):
    """Tests the _ParseCredentialOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    test_tool._ParseCredentialOptions(options)

    # TODO: improve test coverage.

  @shared_test_lib.skipUnlessHasTestFile(['ímynd.dd'])
  def testParseSourcePathOption(self):
    """Tests the _ParseSourcePathOption function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool._ParseSourcePathOption(options)

    options.source = self._GetTestFilePath(['ímynd.dd'])

    test_tool._ParseSourcePathOption(options)

  @shared_test_lib.skipUnlessHasTestFile(['ímynd.dd'])
  def testParseStorageMediaOptions(self):
    """Tests the _ParseStorageMediaOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.partitions = 'all'
    options.source = self._GetTestFilePath(['ímynd.dd'])

    test_tool._ParseStorageMediaImageOptions(options)

  def testParseStorageMediaImageOptions(self):
    """Tests the _ParseStorageMediaImageOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.partitions = 'all'

    test_tool._ParseStorageMediaImageOptions(options)

    # Test if 'partition' option raises in combination with
    # 'partitions' option.
    options = test_lib.TestOptions()
    options.partitions = 'all'
    options.partition = '1'

    with self.assertRaises(errors.BadConfigOption):
      test_tool._ParseStorageMediaImageOptions(options)

    # Test if 'image_offset_bytes' option raises in combination with
    # 'partitions' option.
    options = test_lib.TestOptions()
    options.partitions = 'all'
    options.image_offset_bytes = 512

    with self.assertRaises(errors.BadConfigOption):
      test_tool._ParseStorageMediaImageOptions(options)

    # Test if 'image_offset' option raises in combination with
    # 'partitions' option.
    options = test_lib.TestOptions()
    options.bytes_per_sector = 512
    options.partitions = 'all'
    options.image_offset = 1

    with self.assertRaises(errors.BadConfigOption):
      test_tool._ParseStorageMediaImageOptions(options)

    # TODO: improve test coverage.

  def testParseVSSProcessingOptions(self):
    """Tests the _ParseVSSProcessingOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    test_tool._ParseVSSProcessingOptions(options)

    # TODO: improve test coverage.

  # TODO: add test for _ParseVSSStoresString.
  # TODO: add test for _PromptUserForEncryptedVolumeCredential.
  # TODO: add test for _PromptUserForPartitionIdentifier.
  # TODO: add test for _PromptUserForVSSStoreIdentifiers.
  # TODO: add test for _ScanVolume.
  # TODO: add test for _ScanVolumeScanNode.
  # TODO: add test for _ScanVolumeScanNodeEncrypted.
  # TODO: add test for _ScanVolumeScanNodeVSS.

  def testAddCredentialOptions(self):
    """Tests the AddCredentialOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='storage_media_tool_test.py',
        description='Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddCredentialOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_CREDENTIAL_OPTIONS)

  def testAddStorageMediaImageOptions(self):
    """Tests the AddStorageMediaImageOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='storage_media_tool_test.py',
        description='Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddStorageMediaImageOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS)

  def testAddVSSProcessingOptions(self):
    """Tests the AddVSSProcessingOptions function."""
    argument_parser = argparse.ArgumentParser(
        prog='storage_media_tool_test.py',
        description='Test argument parser.', add_help=False,
        formatter_class=test_lib.SortedArgumentsHelpFormatter)

    test_tool = storage_media_tool.StorageMediaTool()
    test_tool.AddVSSProcessingOptions(argument_parser)

    output = self._RunArgparseFormatHelp(argument_parser)
    self.assertEqual(output, self._EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS)

  @shared_test_lib.skipUnlessHasTestFile(['tsk_volume_system.raw'])
  def testScanSourcePartitionedImage(self):
    """Tests the ScanSource function on a partitioned image."""
    source_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    self._TestScanSourcePartitionedImage(source_path)

  @shared_test_lib.skipUnlessHasTestFile(['image-split.E01'])
  def testScanSourceSplitEWF(self):
    """Tests the ScanSource function on a split EWF image."""
    source_path = self._GetTestFilePath(['image-split.E01'])
    self._TestScanSourcePartitionedImage(source_path)

  @shared_test_lib.skipUnlessHasTestFile(['image.E01'])
  def testScanSourceEWF(self):
    """Tests the ScanSource function on an EWF image."""
    source_path = self._GetTestFilePath(['image.E01'])
    self._TestScanSourceImage(source_path)

  @shared_test_lib.skipUnlessHasTestFile(['image.qcow2'])
  def testScanSourceQCOW(self):
    """Tests the ScanSource function on a QCOW image."""
    source_path = self._GetTestFilePath(['image.qcow2'])
    self._TestScanSourceImage(source_path)

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testScanSourceVSS(self):
    """Tests the ScanSource function on a VSS."""
    source_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._TestScanSourceVSSImage(source_path)

  @shared_test_lib.skipUnlessHasTestFile(['text_parser'])
  def testScanSourceTextDirectory(self):
    """Tests the ScanSource function on a directory."""
    source_path = self._GetTestFilePath(['text_parser'])
    self._TestScanSourceDirectory(source_path)

  @shared_test_lib.skipUnlessHasTestFile(['image.vhd'])
  def testScanSourceVHDI(self):
    """Tests the ScanSource function on a VHD image."""
    source_path = self._GetTestFilePath(['image.vhd'])
    self._TestScanSourceImage(source_path)

  @shared_test_lib.skipUnlessHasTestFile(['image.vmdk'])
  def testScanSourceVMDK(self):
    """Tests the ScanSource function on a VMDK image."""
    source_path = self._GetTestFilePath(['image.vmdk'])
    self._TestScanSourceImage(source_path)

  def testScanSourceNonExisitingFile(self):
    """Tests the ScanSource function on a non existing file."""
    with self.assertRaises(errors.SourceScannerError):
      source_path = self._GetTestFilePath(['nosuchfile.raw'])
      self._TestScanSourceImage(source_path)


if __name__ == '__main__':
  unittest.main()
