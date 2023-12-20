#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage media tool object."""

import argparse
import io
import os
import unittest

try:
  import win32console
except ImportError:
  win32console = None

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.helpers import source_scanner
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver
from dfvfs.volume import apfs_volume_system
from dfvfs.volume import lvm_volume_system
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.cli import storage_media_tool
from plaso.cli import tools
from plaso.lib import errors

from tests.cli import test_lib


class StorageMediaToolMediatorTest(test_lib.CLIToolTestCase):
  """Tests for the storage media tool mediator."""

  # pylint: disable=protected-access

  def testFormatHumanReadableSize(self):
    """Tests the _FormatHumanReadableSize function."""
    test_mediator = storage_media_tool.StorageMediaToolMediator()

    expected_size_string = '1000 B'
    size_string = test_mediator._FormatHumanReadableSize(1000)
    self.assertEqual(size_string, expected_size_string)

    expected_size_string = '1.0KiB / 1.0kB (1024 B)'
    size_string = test_mediator._FormatHumanReadableSize(1024)
    self.assertEqual(size_string, expected_size_string)

    expected_size_string = '976.6KiB / 1.0MB (1000000 B)'
    size_string = test_mediator._FormatHumanReadableSize(1000000)
    self.assertEqual(size_string, expected_size_string)

    expected_size_string = '1.0MiB / 1.0MB (1048576 B)'
    size_string = test_mediator._FormatHumanReadableSize(1048576)
    self.assertEqual(size_string, expected_size_string)

  def testPrintAPFSVolumeIdentifiersOverview(self):
    """Tests the _PrintAPFSVolumeIdentifiersOverview function."""
    test_file_path = self._GetTestFilePath(['apfs.dmg'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_gpt_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.PREFERRED_GPT_BACK_END, location='/p1',
        parent=test_raw_path_spec)
    test_apfs_container_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER, location='/',
        parent=test_gpt_partition_path_spec)

    volume_system = apfs_volume_system.APFSVolumeSystem()
    volume_system.Open(test_apfs_container_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        output_writer=test_output_writer)

    test_mediator._PrintAPFSVolumeIdentifiersOverview(volume_system, ['apfs1'])

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

  def testPrintLVMVolumeIdentifiersOverview(self):
    """Tests the _PrintLVMVolumeIdentifiersOverview function."""
    test_file_path = self._GetTestFilePath(['lvm.raw'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_lvm_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_LVM, location='/',
        parent=test_raw_path_spec)

    volume_system = lvm_volume_system.LVMVolumeSystem()
    volume_system.Open(test_lvm_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        output_writer=test_output_writer)

    test_mediator._PrintLVMVolumeIdentifiersOverview(
        volume_system, ['lvm1', 'lvm2'])

    file_object.seek(0, os.SEEK_SET)
    output_data = file_object.read()

    expected_output_data = [
        b'The following Logical Volume Manager (LVM) volumes were found:',
        b'',
        b'Identifier',
        b'lvm1',
        b'lvm2',
        b'',
        b'']

    if not win32console:
      # Using join here since Python 3 does not support format of bytes.
      expected_output_data[2] = b''.join([
          b'\x1b[1m', expected_output_data[2], b'\x1b[0m'])

    self.assertEqual(output_data.split(b'\n'), expected_output_data)

  def testPrintTSKPartitionIdentifiersOverview(self):
    """Tests the _PrintTSKPartitionIdentifiersOverview function."""
    test_file_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
        parent=test_raw_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(test_tsk_partition_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        output_writer=test_output_writer)

    test_mediator._PrintTSKPartitionIdentifiersOverview(
        volume_system, ['p1', 'p2'])

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

  def testPrintVSSStoreIdentifiersOverview(self):
    """Tests the _PrintVSSStoreIdentifiersOverview function."""
    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=test_os_path_spec)
    test_vss_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, parent=test_qcow_path_spec)

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(test_vss_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        output_writer=test_output_writer)

    test_mediator._PrintVSSStoreIdentifiersOverview(
        volume_system, ['vss1', 'vss2'])

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

  # TODO: add tests for _ReadSelectedVolumes

  def testParseVolumeIdentifiersString(self):
    """Tests the ParseVolumeIdentifiersString function."""
    test_mediator = storage_media_tool.StorageMediaToolMediator()

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('')
    self.assertEqual(volume_identifiers, [])

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('all')
    self.assertEqual(volume_identifiers, ['all'])

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('v1')
    self.assertEqual(volume_identifiers, ['v1'])

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('1')
    self.assertEqual(volume_identifiers, ['v1'])

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('1,3')
    self.assertEqual(volume_identifiers, ['v1', 'v3'])

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('1..3')
    self.assertEqual(volume_identifiers, ['v1', 'v2', 'v3'])

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('v1..v3')
    self.assertEqual(volume_identifiers, ['v1', 'v2', 'v3'])

    volume_identifiers = test_mediator.ParseVolumeIdentifiersString('1..3,5')
    self.assertEqual(volume_identifiers, ['v1', 'v2', 'v3', 'v5'])

    with self.assertRaises(ValueError):
      test_mediator.ParseVolumeIdentifiersString('bogus')

    with self.assertRaises(ValueError):
      test_mediator.ParseVolumeIdentifiersString('1..bogus')

  def testGetAPFSVolumeIdentifiers(self):
    """Tests the GetAPFSVolumeIdentifiers function."""
    test_file_path = self._GetTestFilePath(['apfs.dmg'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_gpt_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.PREFERRED_GPT_BACK_END, location='/p1',
        parent=test_raw_path_spec)
    test_apfs_container_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER, location='/',
        parent=test_gpt_partition_path_spec)

    volume_system = apfs_volume_system.APFSVolumeSystem()
    volume_system.Open(test_apfs_container_path_spec)

    # Test selection of single volume.
    input_file_object = io.BytesIO(b'1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of single volume.
    input_file_object = io.BytesIO(b'apfs1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of single volume with invalid input on first attempt.
    input_file_object = io.BytesIO(b'bogus\napfs1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of all volumes.
    input_file_object = io.BytesIO(b'all\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, ['apfs1'])

    # Test selection of no volumes.
    input_file_object = io.BytesIO(b'\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetAPFSVolumeIdentifiers(
        volume_system, ['apfs1'])

    self.assertEqual(volume_identifiers, [])

  def testGetLVMVolumeIdentifiers(self):
    """Tests the GetLVMVolumeIdentifiers function."""
    test_file_path = self._GetTestFilePath(['lvm.raw'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_lvm_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_LVM, location='/',
        parent=test_raw_path_spec)

    volume_system = lvm_volume_system.LVMVolumeSystem()
    volume_system.Open(test_lvm_path_spec)

    # Test selection of single volume.
    input_file_object = io.BytesIO(b'1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetLVMVolumeIdentifiers(
        volume_system, ['lvm1'])

    self.assertEqual(volume_identifiers, ['lvm1'])

    # Test selection of single volume.
    input_file_object = io.BytesIO(b'lvm1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetLVMVolumeIdentifiers(
        volume_system, ['lvm1'])

    self.assertEqual(volume_identifiers, ['lvm1'])

    # Test selection of single volume with invalid input on first attempt.
    input_file_object = io.BytesIO(b'bogus\nlvm1\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetLVMVolumeIdentifiers(
        volume_system, ['lvm1'])

    self.assertEqual(volume_identifiers, ['lvm1'])

    # Test selection of all volumes.
    input_file_object = io.BytesIO(b'all\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetLVMVolumeIdentifiers(
        volume_system, ['lvm1', 'lvm2'])

    self.assertEqual(volume_identifiers, ['lvm1', 'lvm2'])

    # Test selection of no volumes.
    input_file_object = io.BytesIO(b'\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetLVMVolumeIdentifiers(
        volume_system, ['lvm1'])

    self.assertEqual(volume_identifiers, [])

  def testGetPartitionIdentifiers(self):
    """Tests the GetPartitionIdentifiers function."""
    test_file_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_raw_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_RAW, parent=test_os_path_spec)
    test_tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
        parent=test_raw_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(test_tsk_partition_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        output_writer=test_output_writer)

    # Test selection of single partition.
    input_file_object = io.BytesIO(b'2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p2'])

    # Test selection of single partition.
    input_file_object = io.BytesIO(b'p2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p2'])

    # Test selection of single partition with invalid input on first attempt.
    input_file_object = io.BytesIO(b'bogus\np2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p2'])

    # Test selection of all partitions.
    input_file_object = io.BytesIO(b'all\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetPartitionIdentifiers(
        volume_system, ['p1', 'p2'])

    self.assertEqual(volume_identifiers, ['p1', 'p2'])

    # TODO: test selection of no partitions.

  # TODO: add test for PromptUserForVSSCurrentVolume.

  def testGetVSSStoreIdentifiers(self):
    """Tests the GetVSSStoreIdentifiers function."""
    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    test_os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=test_os_path_spec)
    test_vss_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, parent=test_qcow_path_spec)

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(test_vss_path_spec)

    file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        output_writer=test_output_writer)

    # Test selection of single store.
    input_file_object = io.BytesIO(b'2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss2'])

    # Test selection of single store.
    input_file_object = io.BytesIO(b'vss2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss2'])

    # Test selection of single store with invalid input on first attempt.
    input_file_object = io.BytesIO(b'bogus\nvss2\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss2'])

    # Test selection of all stores.
    input_file_object = io.BytesIO(b'all\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, ['vss1', 'vss2'])

    # Test selection of no stores.
    input_file_object = io.BytesIO(b'\n')
    test_input_reader = tools.FileObjectInputReader(input_file_object)

    output_file_object = io.BytesIO()
    test_output_writer = tools.FileObjectOutputWriter(output_file_object)

    test_mediator = storage_media_tool.StorageMediaToolMediator(
        input_reader=test_input_reader, output_writer=test_output_writer)

    volume_identifiers = test_mediator.GetVSSStoreIdentifiers(
        volume_system, ['vss1', 'vss2'])

    self.assertEqual(volume_identifiers, [])


class StorageMediaToolVolumeScannerTest(test_lib.CLIToolTestCase):
  """Tests for the storage media volume scanner."""

  # pylint: disable=protected-access

  _APFS_PASSWORD = 'apfs-TEST'
  _BDE_PASSWORD = 'bde-TEST'

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

  def _TestScanSourceAPFSImage(self, source_path):
    """Tests the ScanSource function on an APFS image.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.credentials = [('password', '{0:s}'.format(self._APFS_PASSWORD))]
    options.scan_mode = options.SCAN_MODE_ALL
    options.partitions = ['all']
    options.volumes = ['all']

    base_path_specs = []
    scan_context = test_scanner.ScanSource(
        source_path, options, base_path_specs)
    self.assertIsNotNone(scan_context)

    scan_node = scan_context.GetRootScanNode()
    scan_node = scan_node.sub_nodes[0].sub_nodes[0]
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.PREFERRED_GPT_BACK_END)
    if dfvfs_definitions.PREFERRED_GPT_BACK_END == (
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
      expected_number_of_sub_nodes = 6
    else:
      expected_number_of_sub_nodes = 1

    self.assertEqual(len(scan_node.sub_nodes), expected_number_of_sub_nodes)

    for scan_node in scan_node.sub_nodes:
      if getattr(scan_node.path_spec, 'location', None) == '/p1':
        break

    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.PREFERRED_GPT_BACK_END)
    self.assertEqual(len(scan_node.sub_nodes), 1)

    path_spec = scan_node.path_spec
    if dfvfs_definitions.PREFERRED_GPT_BACK_END == (
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
      self.assertEqual(path_spec.start_offset, 20480)

    scan_node = scan_node.sub_nodes[0]
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER)
    self.assertEqual(len(scan_node.sub_nodes), 1)

    scan_node = scan_node.sub_nodes[0]
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator,
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER)
    self.assertEqual(len(scan_node.sub_nodes), 1)

    scan_node = scan_node.sub_nodes[0]
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_APFS)

  def _TestScanSourceDirectory(self, source_path):
    """Tests the ScanSource function on a directory.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL

    base_path_specs = []
    scan_context = test_scanner.ScanSource(
        source_path, options, base_path_specs)
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
    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL

    base_path_specs = []
    scan_context = test_scanner.ScanSource(
        source_path, options, base_path_specs)
    self.assertIsNotNone(scan_context)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.PREFERRED_EXT_BACK_END)

  def _TestScanSourceLVMImage(self, source_path):
    """Tests the ScanSource function on a LVM image.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL
    options.partitions = ['all']
    options.volumes = ['all']

    base_path_specs = []
    scan_context = test_scanner.ScanSource(
        source_path, options, base_path_specs)
    self.assertIsNotNone(scan_context)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_LVM)
    self.assertEqual(len(scan_node.sub_nodes), 2)

    scan_node = scan_node.sub_nodes[0]
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_LVM)
    self.assertEqual(len(scan_node.sub_nodes), 1)

    scan_node = scan_node.sub_nodes[0]
    self.assertIsNotNone(scan_node)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.PREFERRED_EXT_BACK_END)

  def _TestScanSourcePartitionedImage(self, source_path):
    """Tests the ScanSource function on an image containing multiple partitions.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL
    options.partitions = ['all']

    base_path_specs = []
    scan_context = test_scanner.ScanSource(
        source_path, options, base_path_specs)
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
        scan_node.type_indicator, dfvfs_definitions.PREFERRED_EXT_BACK_END)

  def _TestScanSourceVSSImage(self, source_path):
    """Tests the ScanSource function on a VSS storage media image.

    Args:
      source_path (str): path of the source device, directory or file.
    """
    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL
    options.partitions = ['all']
    options.snapshots = ['all']
    options.volumes = ['all']

    base_path_specs = []
    scan_context = test_scanner.ScanSource(
        source_path, options, base_path_specs)
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
        scan_node.type_indicator, dfvfs_definitions.PREFERRED_NTFS_BACK_END)

  def testScanEncryptedVolumeOnBDE(self):
    """Tests the _ScanEncryptedVolume function on a BDE image."""
    test_file_path = self._GetTestFilePath(['bdetogo.raw'])
    self._SkipIfPathNotExists(test_file_path)

    resolver.Resolver.key_chain.Empty()

    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.credentials = [('password', self._BDE_PASSWORD)]

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_file_path)

    test_scanner._source_scanner.Scan(scan_context)
    scan_node = self._GetTestScanNode(scan_context)

    bde_scan_node = scan_node.sub_nodes[0]

    test_scanner._ScanEncryptedVolume(scan_context, bde_scan_node, options)

  def testScanVolumeSystemRoot(self):
    """Tests the _ScanVolumeSystemRoot function."""
    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL

    scan_context = source_scanner.SourceScannerContext()

    # Test error conditions.
    with self.assertRaises(dfvfs_errors.ScannerError):
      test_scanner._ScanVolumeSystemRoot(scan_context, None, options, [])

    scan_node = source_scanner.SourceScanNode(None)
    with self.assertRaises(dfvfs_errors.ScannerError):
      test_scanner._ScanVolumeSystemRoot(scan_context, scan_node, options, [])

  def testScanVolumeSystemRootOnAPFS(self):
    """Tests the _ScanVolumeSystemRoot function on an APFS image."""
    test_file_path = self._GetTestFilePath(['apfs.dmg'])
    self._SkipIfPathNotExists(test_file_path)

    resolver.Resolver.key_chain.Empty()

    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL
    options.volumes = ['all']

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_file_path)

    test_scanner._source_scanner.Scan(scan_context)
    scan_node = scan_context.GetRootScanNode()
    scan_node = scan_node.sub_nodes[0].sub_nodes[0]

    if dfvfs_definitions.PREFERRED_GPT_BACK_END == (
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
      apfs_container_scan_node = scan_node.sub_nodes[4].sub_nodes[0]
    else:
      apfs_container_scan_node = scan_node.sub_nodes[0].sub_nodes[0]

    base_path_specs = []
    test_scanner._ScanVolumeSystemRoot(
        scan_context, apfs_container_scan_node, options, base_path_specs)
    self.assertEqual(len(base_path_specs), 1)

    # Test error conditions.
    with self.assertRaises(dfvfs_errors.ScannerError):
      test_scanner._ScanVolumeSystemRoot(
          scan_context, apfs_container_scan_node.sub_nodes[0], options,
          base_path_specs)

  def testScanVolumeSystemRootOnLVM(self):
    """Tests the _ScanVolumeSystemRoot function on a LVM image."""
    test_file_path = self._GetTestFilePath(['lvm.raw'])
    self._SkipIfPathNotExists(test_file_path)

    resolver.Resolver.key_chain.Empty()

    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL
    options.volumes = ['all']

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_file_path)

    test_scanner._source_scanner.Scan(scan_context)
    lvm_scan_node = self._GetTestScanNode(scan_context)

    base_path_specs = []
    test_scanner._ScanVolumeSystemRoot(
        scan_context, lvm_scan_node, options, base_path_specs)
    self.assertEqual(len(base_path_specs), 1)

    # Test error conditions.
    with self.assertRaises(dfvfs_errors.ScannerError):
      test_scanner._ScanVolumeSystemRoot(
          scan_context, lvm_scan_node.sub_nodes[0], options, base_path_specs)

  def testScanVolumeSystemRootOnPartitionedImage(self):
    """Tests the _ScanVolumeSystemRoot function on a partitioned image."""
    test_file_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    self._SkipIfPathNotExists(test_file_path)

    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_file_path)

    test_scanner._source_scanner.Scan(scan_context)
    scan_node = self._GetTestScanNode(scan_context)

    # Test error conditions.
    with self.assertRaises(dfvfs_errors.ScannerError):
      test_scanner._ScanVolumeSystemRoot(scan_context, scan_node, options, [])

  def testScanVolumeSystemRootOnVSS(self):
    """Tests the _ScanVolumeSystemRoot function on VSS."""
    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_SNAPSHOTS_ONLY
    options.snapshots = ['all']

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_file_path)

    test_scanner._source_scanner.Scan(scan_context)
    scan_node = self._GetTestScanNode(scan_context)

    vss_scan_node = scan_node.sub_nodes[0]

    base_path_specs = []
    test_scanner._ScanVolumeSystemRoot(
        scan_context, vss_scan_node, options, base_path_specs)
    self.assertEqual(len(base_path_specs), 2)

  def testScanVolumeSystemRootOnVSSDisabled(self):
    """Tests the _ScanVolumeSystemRoot function on VSS with VSS turned off."""
    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    test_scanner = storage_media_tool.StorageMediaToolVolumeScanner()

    options = storage_media_tool.StorageMediaToolVolumeScannerOptions()
    options.scan_mode = options.SCAN_MODE_ALL
    options.snapshots = ['none']

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(test_file_path)

    test_scanner._source_scanner.Scan(scan_context)
    scan_node = self._GetTestScanNode(scan_context)

    vss_scan_node = scan_node.sub_nodes[0]

    base_path_specs = []
    test_scanner._ScanVolumeSystemRoot(
        scan_context, vss_scan_node, options, base_path_specs)
    self.assertEqual(len(base_path_specs), 0)

  def testScanSourceAPFS(self):
    """Tests the ScanSource function on an APFS image."""
    source_path = self._GetTestFilePath(['apfs.dmg'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceAPFSImage(source_path)

  def testScanSourceEncryptedAPFS(self):
    """Tests the ScanSource function on an encrypted APFS image."""
    resolver.Resolver.key_chain.Empty()

    source_path = self._GetTestFilePath(['apfs_encrypted.dmg'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceAPFSImage(source_path)

  def testScanSourcePartitionedImage(self):
    """Tests the ScanSource function on a partitioned image."""
    source_path = self._GetTestFilePath(['tsk_volume_system.raw'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourcePartitionedImage(source_path)

  def testScanSourceSplitEWF(self):
    """Tests the ScanSource function on a split EWF image."""
    source_path = self._GetTestFilePath(['image-split.E01'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourcePartitionedImage(source_path)

  def testScanSourceEWF(self):
    """Tests the ScanSource function on an EWF image."""
    source_path = self._GetTestFilePath(['image.E01'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceImage(source_path)

  def testScanSourceLVM(self):
    """Tests the ScanSource function on a LVM image."""
    source_path = self._GetTestFilePath(['lvm.raw'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceLVMImage(source_path)

  def testScanSourceNonExisitingFile(self):
    """Tests the ScanSource function on a non existing file."""
    with self.assertRaises(dfvfs_errors.ScannerError):
      source_path = self._GetTestFilePath(['nosuchfile.raw'])
      self._TestScanSourceImage(source_path)

  def testScanSourceQCOW(self):
    """Tests the ScanSource function on a QCOW image."""
    source_path = self._GetTestFilePath(['image.qcow2'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceImage(source_path)

  def testScanSourceTextDirectory(self):
    """Tests the ScanSource function on a directory."""
    source_path = self._GetTestFilePath(['text_parser'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceDirectory(source_path)

  def testScanSourceVHDI(self):
    """Tests the ScanSource function on a VHD image."""
    source_path = self._GetTestFilePath(['image.vhd'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceImage(source_path)

  def testScanSourceVMDK(self):
    """Tests the ScanSource function on a VMDK image."""
    source_path = self._GetTestFilePath(['image.vmdk'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceImage(source_path)

  def testScanSourceVSS(self):
    """Tests the ScanSource function on a VSS."""
    source_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(source_path)

    self._TestScanSourceVSSImage(source_path)


class StorageMediaToolTest(test_lib.CLIToolTestCase):
  """Tests for the storage media tool."""

  # pylint: disable=protected-access

  _APFS_PASSWORD = 'apfs-TEST'
  _BDE_PASSWORD = 'bde-TEST'

  _EXPECTED_OUTPUT_CREDENTIAL_OPTIONS = """\
usage: storage_media_tool_test.py [--credential TYPE:DATA]

Test argument parser.

{0:s}:
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
""".format(test_lib.ARGPARSE_OPTIONS)

  _EXPECTED_OUTPUT_STORAGE_MEDIA_OPTIONS = """\
usage: storage_media_tool_test.py [--partitions PARTITIONS]
                                  [--volumes VOLUMES]

Test argument parser.

{0:s}:
  --partitions PARTITIONS, --partition PARTITIONS
                        Define partitions to be processed. A range of
                        partitions can be defined as: "3..5". Multiple
                        partitions can be defined as: "1,3,5" (a list of comma
                        separated values). Ranges and lists can also be
                        combined as: "1,3..5". The first partition is 1. All
                        partitions can be specified with: "all".
  --volumes VOLUMES, --volume VOLUMES
                        Define volumes to be processed. A range of volumes can
                        be defined as: "3..5". Multiple volumes can be defined
                        as: "1,3,5" (a list of comma separated values). Ranges
                        and lists can also be combined as: "1,3..5". The first
                        volume is 1. All volumes can be specified with: "all".
""".format(test_lib.ARGPARSE_OPTIONS)

  _EXPECTED_OUTPUT_VSS_PROCESSING_OPTIONS = """\
usage: storage_media_tool_test.py [--no_vss] [--vss_only]
                                  [--vss_stores VSS_STORES]

Test argument parser.

{0:s}:
  --no_vss, --no-vss    Do not scan for Volume Shadow Snapshots (VSS). This
                        means that Volume Shadow Snapshots (VSS) are not
                        processed. WARNING: this option is deprecated use
                        --vss_stores=none instead.
  --vss_only, --vss-only
                        Do not process the current volume if Volume Shadow
                        Snapshots (VSS) have been selected.
  --vss_stores VSS_STORES, --vss-stores VSS_STORES
                        Define Volume Shadow Snapshots (VSS) (or stores) that
                        need to be processed. A range of snapshots can be
                        defined as: "3..5". Multiple snapshots can be defined
                        as: "1,3,5" (a list of comma separated values). Ranges
                        and lists can also be combined as: "1,3..5". The first
                        snapshot is 1. All snapshots can be defined as: "all"
                        and no snapshots as: "none".
""".format(test_lib.ARGPARSE_OPTIONS)

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

  def testParseCredentialOptions(self):
    """Tests the _ParseCredentialOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    test_tool._ParseCredentialOptions(options)

    # TODO: improve test coverage.

  def testParseSourcePathOption(self):
    """Tests the _ParseSourcePathOption function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool._ParseSourcePathOption(options)

    options.source = test_file_path

    test_tool._ParseSourcePathOption(options)

  def testParseStorageMediaOptions(self):
    """Tests the _ParseStorageMediaOptions function."""
    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.partitions = 'all'
    options.source = test_file_path

    test_tool._ParseStorageMediaImageOptions(options)

  def testParseStorageMediaImageOptions(self):
    """Tests the _ParseStorageMediaImageOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()
    options.partitions = 'all'

    test_tool._ParseStorageMediaImageOptions(options)

    # TODO: improve test coverage.
  def testParseVSSProcessingOptions(self):
    """Tests the _ParseVSSProcessingOptions function."""
    test_tool = storage_media_tool.StorageMediaTool()

    options = test_lib.TestOptions()

    test_tool._ParseVSSProcessingOptions(options)

    # TODO: improve test coverage.

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


if __name__ == '__main__':
  unittest.main()
