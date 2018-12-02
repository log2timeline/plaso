#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the storage media tool object."""

from __future__ import unicode_literals

import argparse
import io
import os
import unittest

try:
  import win32console
except ImportError:
  win32console = None

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.helpers import source_scanner
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import fake_path_spec
from dfvfs.resolver import resolver
from dfvfs.volume import apfs_volume_system
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import storage_media_tool
from plaso.cli import tools
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class StorageMediaToolTest(test_lib.CLIToolTestCase):
  """Tests for the storage media tool object."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT_CREDENTIAL_OPTIONS = """\
usage: storage_media_tool_test.py [--credential TYPE:DATA]

Test argument parser.

optional arguments:
  --credential TYPE:DATA
                        Define a credentials that can be used to unlock
                        encrypted volumes e.g. BitLocker. The credential is
                        defined as type:data e.g. "password:BDE-test".
                        Supported credential types are: key_data, password,
                        recovery_password, startup_key. Binary key data is
                        expected to be passed in BASE-16 encoding
                        (hexadecimal). WARNING credentials passed via command
                        line arguments can end up in logs, so use this option
                        with care.
"""

  _EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS = """\
usage: storage_media_tool_test.py [--partitions PARTITIONS]
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
  --partitions PARTITIONS, --partition PARTITIONS
                        Define partitions to be processed. A range of
                        partitions can be defined as: "3..5". Multiple
                        partitions can be defined as: "1,3,5" (a list of comma
                        separated values). Ranges and lists can also be
                        combined as: "1,3..5". The first partition is 1. All
                        partitions can be specified with: "all".
  --sector_size BYTES_PER_SECTOR, --sector-size BYTES_PER_SECTOR
                        The number of bytes per sector, which is 512 by
                        default.
"""

  _EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS = """\
usage: storage_media_tool_test.py [--no_vss] [--vss_only]
                                  [--vss_stores VSS_STORES]

Test argument parser.

optional arguments:
  --no_vss, --no-vss    Do not scan for Volume Shadow Snapshots (VSS). This
                        means that Volume Shadow Snapshots (VSS) are not
                        processed.
  --vss_only, --vss-only
                        Do not process the current volume if Volume Shadow
                        Snapshots (VSS) have been selected.
  --vss_stores VSS_STORES, --vss-stores VSS_STORES
                        Define Volume Shadow Snapshots (VSS) (or stores that
                        need to be processed. A range of stores can be defined
                        as: "3..5". Multiple stores can be defined as: "1,3,5"
                        (a list of comma separated values). Ranges and lists
                        can also be combined as: "1,3..5". The first store is
                        1. All stores can be defined as: "all".
"""

  def _GetTestScanNode(self, scan_context):
    """Retrieves the scan node for testing.

    Retrieves the first scan node, from the root upwards, with more or less
    than 1 sub node.

    Args:
      scan_context (dfvfs.ScanContext): scan context.

    Returns:
      dfvfs.SourceScanNode: scan node.
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

  # TODO: add test for _GetAPFSVolumeIdentifiers.
  # TODO: add test for _GetTSKPartitionIdentifiers.
  # TODO: add test for _GetVSSStoreIdentifiers.

  @shared_test_lib.skipUnlessHasTestFile(['tsk_volume_system.raw'])
  def testNormalizedVolumeIdentifiersPartitionedImage(self):
    """Tests the _NormalizedVolumeIdentifiers function."""
    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
        parent=test_raw_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(test_tsk_partition_path_spec)

    volume_identifiers = test_tool._NormalizedVolumeIdentifiers(
        volume_system, ['p1', 'p2'], prefix='p')
    self.assertEqual(volume_identifiers, ['p1', 'p2'])

    volume_identifiers = test_tool._NormalizedVolumeIdentifiers(
        volume_system, [1, 2], prefix='p')
    self.assertEqual(volume_identifiers, ['p1', 'p2'])

    # Test error conditions.
    with self.assertRaises(errors.SourceScannerError):
      test_tool._NormalizedVolumeIdentifiers(
          volume_system, ['p3'], prefix='p')

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testNormalizedVolumeIdentifiersVSS(self):
    """Tests the _NormalizedVolumeIdentifiers function on a VSS."""
    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=test_os_path_spec)
    test_vss_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, parent=test_qcow_path_spec)

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(test_vss_path_spec)

    volume_identifiers = test_tool._NormalizedVolumeIdentifiers(
        volume_system, ['vss1', 'vss2'], prefix='vss')
    self.assertEqual(volume_identifiers, ['vss1', 'vss2'])

    volume_identifiers = test_tool._NormalizedVolumeIdentifiers(
        volume_system, [1, 2], prefix='vss')
    self.assertEqual(volume_identifiers, ['vss1', 'vss2'])

    # Test error conditions.
    with self.assertRaises(errors.SourceScannerError):
      test_tool._NormalizedVolumeIdentifiers(
          volume_system, ['vss3'], prefix='vss')

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

  def testParseVolumeIdentifiersString(self):
    """Tests the _ParseVolumeIdentifiersString function."""
    test_tool = storage_media_tool.StorageMediaTool()

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('')
    self.assertEqual(volume_identifiers, [])

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('all')
    self.assertEqual(volume_identifiers, ['all'])

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('v1')
    self.assertEqual(volume_identifiers, ['v1'])

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('1')
    self.assertEqual(volume_identifiers, ['v1'])

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('1,3')
    self.assertEqual(volume_identifiers, ['v1', 'v3'])

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('1..3')
    self.assertEqual(volume_identifiers, ['v1', 'v2', 'v3'])

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('v1..v3')
    self.assertEqual(volume_identifiers, ['v1', 'v2', 'v3'])

    volume_identifiers = test_tool._ParseVolumeIdentifiersString('1..3,5')
    self.assertEqual(volume_identifiers, ['v1', 'v2', 'v3', 'v5'])

    with self.assertRaises(ValueError):
      test_tool._ParseVolumeIdentifiersString('bogus')

    with self.assertRaises(ValueError):
      test_tool._ParseVolumeIdentifiersString('1..bogus')

  def testParseVSSProcessingOptions(self):
    """Tests the _ParseVSSProcessingOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    test_tool._ParseVSSProcessingOptions(options)

    # TODO: improve test coverage.

  @shared_test_lib.skipUnlessHasTestFile(['apfs.dmg'])
  def testPrintAPFSVolumeIdentifiersOverview(self):
    """Tests the _PrintAPFSVolumeIdentifiersOverview function."""
    test_path = self._GetTestFilePath(['apfs.dmg'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p1',
        parent=test_raw_path_spec)
    test_apfs_container_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER, location='/',
        parent=test_tsk_partition_path_spec)

    volume_system = apfs_volume_system.APFSVolumeSystem()
    volume_system.Open(test_apfs_container_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        output_writer=test_output_writer)

    test_tool._PrintAPFSVolumeIdentifiersOverview(volume_system, ['apfs1'])

    file_object.seek(0, os.SEEK_SET)
    output_data = file_object.read()

    expected_output_data = [
        b'The following Apple File System (APFS) volumes were found:',
        b'',
        b'Identifier      Name',
        b'apfs1           SingleVolume',
        b'',
        b'']

    if not win32console:
      # Using join here since Python 3 does not support format of bytes.
      expected_output_data[2] = b''.join([
          b'\x1b[1m', expected_output_data[2], b'\x1b[0m'])

    self.assertEqual(output_data.split(b'\n'), expected_output_data)

  @shared_test_lib.skipUnlessHasTestFile(['tsk_volume_system.raw'])
  def testPrintTSKPartitionIdentifiersOverview(self):
    """Tests the _PrintTSKPartitionIdentifiersOverview function."""
    test_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
        parent=test_raw_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(test_tsk_partition_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        output_writer=test_output_writer)

    test_tool._PrintTSKPartitionIdentifiersOverview(volume_system, ['p1', 'p2'])

    file_object.seek(0, os.SEEK_SET)
    output_data = file_object.read()

    expected_output_data = [
        b'The following partitions were found:',
        b'',
        b'Identifier      Offset (in bytes)       Size (in bytes)',
        (b'p1              512 (0x00000200)        175.0KiB / 179.2kB '
         b'(179200 B)'),
        b'p2              180224 (0x0002c000)     1.2MiB / 1.3MB (1294336 B)',
        b'',
        b'']

    if not win32console:
      # Using join here since Python 3 does not support format of bytes.
      expected_output_data[2] = b''.join([
          b'\x1b[1m', expected_output_data[2], b'\x1b[0m'])

    self.assertEqual(output_data.split(b'\n'), expected_output_data)

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testPrintVSSStoreIdentifiersOverview(self):
    """Tests the _PrintVSSStoreIdentifiersOverview function."""
    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=test_os_path_spec)
    test_vss_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, parent=test_qcow_path_spec)

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(test_vss_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        output_writer=test_output_writer)

    test_tool._PrintVSSStoreIdentifiersOverview(volume_system, ['vss1', 'vss2'])

    file_object.seek(0, os.SEEK_SET)
    output_data = file_object.read()

    expected_output_data = [
        b'The following Volume Shadow Snapshots (VSS) were found:',
        b'',
        b'Identifier      Creation Time',
        b'vss1            2013-12-03 06:35:09.7363787',
        b'vss2            2013-12-03 06:37:48.9190583',
        b'',
        b'']

    if not win32console:
      # Using join here since Python 3 does not support format of bytes.
      expected_output_data[2] = b''.join([
          b'\x1b[1m', expected_output_data[2], b'\x1b[0m'])

    self.assertEqual(output_data.split(b'\n'), expected_output_data)

  @shared_test_lib.skipUnlessHasTestFile(['apfs.dmg'])
  def testPromptUserForAPFSVolumeIdentifiers(self):
    """Tests the _PromptUserForAPFSVolumeIdentifiers function."""
    test_path = self._GetTestFilePath(['apfs.dmg'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p1',
        parent=test_raw_path_spec)
    test_apfs_container_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER, location='/',
        parent=test_tsk_partition_path_spec)

    volume_system = apfs_volume_system.APFSVolumeSystem()
    volume_system.Open(test_apfs_container_path_spec)

    # Test selection of single volume.
    input_file_object = io.BytesIO(b'1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of single volume.
    input_file_object = io.BytesIO(b'apfs1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of single volume with invalid input on first attempt.
    input_file_object = io.BytesIO(b'bogus\napfs1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of all volumes.
    input_file_object = io.BytesIO(b'all\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of no volumes.
    input_file_object = io.BytesIO(b'\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, [])

  # TODO: add test for _PromptUserForEncryptedVolumeCredential.

  @shared_test_lib.skipUnlessHasTestFile(['tsk_volume_system.raw'])
  def testPromptUserForPartitionIdentifiers(self):
    """Tests the _PromptUserForPartitionIdentifiers function."""
    test_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
        parent=test_raw_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(test_tsk_partition_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        output_writer=test_output_writer)

    # Test selection of single partition.
    input_file_object = io.BytesIO(b'2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p2'])

    # Test selection of single partition.
    input_file_object = io.BytesIO(b'p2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p2'])

    # Test selection of single partition with invalid input on first attempt.
    input_file_object = io.BytesIO(b'bogus\np2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p2'])

    # Test selection of all partitions.
    input_file_object = io.BytesIO(b'all\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p1', 'p2'])

    # Test selection of no partitions.
    input_file_object = io.BytesIO(b'\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, [])

  # TODO: add test for _PromptUserForVSSCurrentVolume.

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testPromptUserForVSSStoreIdentifiers(self):
    """Tests the _PromptUserForVSSStoreIdentifiers function."""
    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    test_qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=test_os_path_spec)
    test_vss_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, parent=test_qcow_path_spec)

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(test_vss_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        output_writer=test_output_writer)

    # Test selection of single store.
    input_file_object = io.BytesIO(b'2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss2'])

    # Test selection of single store.
    input_file_object = io.BytesIO(b'vss2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss2'])

    # Test selection of single store with invalid input on first attempt.
    input_file_object = io.BytesIO(b'bogus\nvss2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss2'])

    # Test selection of all stores.
    input_file_object = io.BytesIO(b'all\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss1', 'vss2'])

    # Test selection of no stores.
    input_file_object = io.BytesIO(b'\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_tool = storage_media_tool.StorageMediaTool(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_tool._PromptUserForVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, [])

  # TODO: add tests for _ReadSelectedVolumes.

  def testScanFileSystem(self):
    """Tests the _ScanFileSystem function."""
    test_tool = storage_media_tool.StorageMediaTool()

    path_spec = fake_path_spec.FakePathSpec(location='/')
    scan_node = source_scanner.SourceScanNode(path_spec)

    base_path_specs = []
    test_tool._ScanFileSystem(scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 1)

    # Test error conditions.
    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanFileSystem(None, [])

    scan_node = source_scanner.SourceScanNode(None)
    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanFileSystem(scan_node, [])

  def testScanVolume(self):
    """Tests the _ScanVolume function."""
    test_tool = storage_media_tool.StorageMediaTool()

    # Test error conditions.
    scan_context = source_scanner.SourceScannerContext()

    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanVolume(scan_context, None, [])

    volume_scan_node = source_scanner.SourceScanNode(None)
    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanVolume(scan_context, volume_scan_node, [])

  @shared_test_lib.skipUnlessHasTestFile(['apfs.dmg'])
  def testScanVolumeOnAPFS(self):
    """Tests the _ScanVolume function on an APFS image."""
    resolver.Resolver.key_chain.Empty()

    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['apfs.dmg'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    volume_scan_node = self._GetTestScanNode(scan_context)

    apfs_container_scan_node = volume_scan_node.sub_nodes[4].sub_nodes[0]

    base_path_specs = []
    test_tool._ScanVolume(
        scan_context, apfs_container_scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 1)

  # TODO: add testScanVolumeOnBDE from dfvfs

  @shared_test_lib.skipUnlessHasTestFile(['ímynd.dd'])
  def testScanVolumeOnRAW(self):
    """Tests the _ScanVolume function on a RAW image."""
    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['ímynd.dd'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    volume_scan_node = scan_context.GetRootScanNode()

    base_path_specs = []
    test_tool._ScanVolume(scan_context, volume_scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 1)

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testScanVolumeOnVSS(self):
    """Tests the _ScanVolume function on VSS."""
    test_tool = storage_media_tool.StorageMediaTool()
    test_tool._process_vss = True
    test_tool._vss_only = False
    test_tool._vss_stores = ['all']

    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    volume_scan_node = self._GetTestScanNode(scan_context)

    base_path_specs = []
    test_tool._ScanVolume(
        scan_context, volume_scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 3)

  def testScanVolumeScanNode(self):
    """Tests the _ScanVolumeScanNode function."""
    test_tool = storage_media_tool.StorageMediaTool()

    # Test error conditions.
    scan_context = source_scanner.SourceScannerContext()

    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanVolumeScanNode(scan_context, None, [])

    volume_scan_node = source_scanner.SourceScanNode(None)
    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanVolumeScanNode(scan_context, volume_scan_node, [])

  @shared_test_lib.skipUnlessHasTestFile(['apfs.dmg'])
  def testScanVolumeScanNodeOnAPFS(self):
    """Tests the _ScanVolumeScanNode function on an APFS image."""
    resolver.Resolver.key_chain.Empty()

    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['apfs.dmg'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    volume_scan_node = self._GetTestScanNode(scan_context)

    apfs_container_scan_node = volume_scan_node.sub_nodes[4].sub_nodes[0]

    base_path_specs = []
    test_tool._ScanVolumeScanNode(
        scan_context, apfs_container_scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 1)

  # TODO: add testScanVolumeScanNodeOnBDE from dfvfs

  @shared_test_lib.skipUnlessHasTestFile(['ímynd.dd'])
  def testScanVolumeScanNodeOnRAW(self):
    """Tests the _ScanVolumeScanNode function on a RAW image."""
    test_tool = storage_media_tool.StorageMediaTool()

    test_path = self._GetTestFilePath(['ímynd.dd'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    volume_scan_node = scan_context.GetRootScanNode()

    base_path_specs = []
    test_tool._ScanVolumeScanNode(
        scan_context, volume_scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 1)

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testScanVolumeScanNodeOnVSS(self):
    """Tests the _ScanVolumeScanNode function on VSS."""
    test_tool = storage_media_tool.StorageMediaTool()
    test_tool._process_vss = True
    test_tool._vss_only = False
    test_tool._vss_stores = ['all']

    # Test function on VSS root.
    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    test_tool._process_vss = True
    test_tool._vss_only = False
    test_tool._vss_stores = ['all']
    volume_scan_node = self._GetTestScanNode(scan_context)

    base_path_specs = []
    test_tool._ScanVolumeScanNode(
        scan_context, volume_scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 0)

    # Test function on VSS volume.
    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    test_tool._process_vss = True
    test_tool._vss_only = False
    test_tool._vss_stores = ['all']
    volume_scan_node = self._GetTestScanNode(scan_context)

    base_path_specs = []
    test_tool._ScanVolumeScanNode(
        scan_context, volume_scan_node.sub_nodes[0], base_path_specs)
    self.assertEqual(len(base_path_specs), 2)

  # TODO: add tests for _ScanVolumeScanNodeEncrypted.

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  def testScanVolumeScanNodeVSS(self):
    """Tests the _ScanVolumeScanNodeVSS function."""
    test_tool = storage_media_tool.StorageMediaTool()
    test_tool._process_vss = True
    test_tool._vss_only = False
    test_tool._vss_stores = ['all']

    # Test function on VSS root.
    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    volume_scan_node = scan_context.GetRootScanNode()

    base_path_specs = []
    test_tool._ScanVolumeScanNodeVSS(volume_scan_node, base_path_specs)
    self.assertEqual(len(base_path_specs), 0)

    # Test function on VSS volume.
    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_path)

    test_tool._source_scanner.Scan(scan_context)
    volume_scan_node = self._GetTestScanNode(scan_context)

    base_path_specs = []
    test_tool._ScanVolumeScanNodeVSS(
        volume_scan_node.sub_nodes[0], base_path_specs)
    self.assertEqual(len(base_path_specs), 2)

    # Test error conditions.
    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanVolumeScanNodeVSS(None, [])

    volume_scan_node = source_scanner.SourceScanNode(None)
    with self.assertRaises(errors.SourceScannerError):
      test_tool._ScanVolumeScanNodeVSS(volume_scan_node, [])

  # TODO: add tests for _UnlockEncryptedVolumeScanNode

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

  @shared_test_lib.skipUnlessHasTestFile(['apfs.E01'])
  def testScanSourceAPFS(self):
    """Tests the ScanSource function on an APFS image."""
    source_path = self._GetTestFilePath(['apfs.E01'])
    self._TestScanSourceImage(source_path)

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
