#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the NTFS metadata file parser."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.parsers import ntfs

from tests.parsers import test_lib


class NTFSMFTParserTest(test_lib.ParserTestCase):
  """Tests for NTFS $MFT metadata file parser."""

  def testParseFile(self):
    """Tests the Parse function on a stand-alone $MFT file."""
    parser = ntfs.NTFSMFTParser()

    test_file_path = self._GetTestFilePath(['MFT'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    storage_writer = self._ParseFileByPathSpec(os_path_spec, parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 31642)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test path hints of a regular file.
    expected_event_values = {
        'access_time': '2007-06-30T12:58:50.2740544+00:00',
        'creation_time': '2007-06-30T12:58:50.2740544+00:00',
        'data_type': 'fs:stat:ntfs',
        'entry_modification_time': '2007-06-30T12:58:50.2740544+00:00',
        'modification_time': '2007-06-30T12:58:50.2740544+00:00',
        'name': 'SAM',
        'path_hints': ['\\WINDOWS\\system32\\config\\SAM']}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7204)
    self.CheckEventData(event_data, expected_event_values)

    # Test path hints of a deleted file.
    expected_path_hints = [(
        '\\Documents and Settings\\Donald Blake\\Local Settings\\'
        'Temporary Internet Files\\Content.IE5\\9EUWFPZ1\\CAJA1S19.js')]

    expected_event_values = {
        'access_time': '2009-01-14T03:38:58.5869993+00:00',
        'creation_time': '2009-01-14T03:38:58.5869993+00:00',
        'data_type': 'fs:stat:ntfs',
        'entry_modification_time': '2009-01-14T03:38:58.5869993+00:00',
        'is_allocated': False,
        'modification_time': '2009-01-14T03:38:58.5869993+00:00',
        'name': 'CAJA1S19.js',
        'path_hints': expected_path_hints}

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', 30173)
    self.CheckEventData(event_data, expected_event_values)

    # Testing path hint of orphaned file.
    expected_event_values = {
        'access_time': '2009-01-14T21:07:11.5721856+00:00',
        'creation_time': '2009-01-14T21:07:11.5721856+00:00',
        'data_type': 'fs:stat:ntfs',
        'entry_modification_time': '2009-01-14T21:07:11.5721856+00:00',
        'is_allocated': False,
        'modification_time': '2009-01-14T21:07:11.5721856+00:00',
        'name': 'menu.text.css',
        'path_hints': ['$Orphan\\session\\menu.text.css']}

    event_data = storage_writer.GetAttributeContainerByIndex(
        'event_data', 31412)
    self.CheckEventData(event_data, expected_event_values)

    # Test distributed link tracking event data.
    expected_event_values = {
        'creation_time': '2007-06-30T12:58:40.5000041+00:00',
        'data_type': 'windows:distributed_link_tracking:creation',
        'mac_address': 'db:30:99:be:ae:3c',
        'origin': '$MFT: 462-1',
        'uuid': '9fe44b69-2709-11dc-a06b-db3099beae3c'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 920)
    self.CheckEventData(event_data, expected_event_values)

  def testParseImage(self):
    """Tests the Parse function on a storage media image."""
    parser = ntfs.NTFSMFTParser()

    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=0, location='/$MFT',
        parent=qcow_path_spec)

    storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 71)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2013-12-03T06:30:41.8079077+00:00',
        'attribute_type': 0x00000030,
        'creation_time': '2013-12-03T06:30:41.8079077+00:00',
        'data_type': 'fs:stat:ntfs',
        'entry_modification_time': '2013-12-03T06:30:41.8079077+00:00',
        'file_reference': 0x1000000000000,
        'is_allocated': True,
        'modification_time': '2013-12-03T06:30:41.8079077+00:00',
        'name': '$MFT',
        'parent_file_reference': 0x5000000000005,
        'path_hints': ['\\$MFT']}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Note that the source file is a RAW (VMDK flat) image.
    test_file_path = self._GetTestFilePath(['multi_partition_image.vmdk'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    p2_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p2',
        part_index=3, start_offset=0x00510000, parent=os_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=0, location='/$MFT',
        parent=p2_path_spec)

    storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 46)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2015-05-15T01:00:26.8925979+00:00',
        'attribute_type': 0x00000030,
        'creation_time': '2015-05-15T01:00:26.8925979+00:00',
        'data_type': 'fs:stat:ntfs',
        'entry_modification_time': '2015-05-15T01:00:26.8925979+00:00',
        'file_reference': 0x1000000000000,
        'is_allocated': True,
        'modification_time': '2015-05-15T01:00:26.8925979+00:00',
        'name': '$MFT',
        'parent_file_reference': 0x5000000000005,
        'path_hints': ['\\$MFT']}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class NTFSUsnJrnlParser(test_lib.ParserTestCase):
  """Tests for NTFS $UsnJrnl metadata file parser."""

  def testParseImage(self):
    """Tests the Parse function on a storage media image."""
    parser = ntfs.NTFSUsnJrnlParser()

    test_file_path = self._GetTestFilePath(['usnjrnl.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p1',
        part_index=2, start_offset=0x00007e00, parent=qcow_path_spec)

    # To be able to ignore the sparse data ranges the UsnJrnl parser
    # requires to read directly from the volume.
    storage_writer = self._ParseFileByPathSpec(volume_path_spec, parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 19)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'fs:ntfs:usn_change',
        'filename': 'Nieuw - Tekstdocument.txt',
        'file_reference': 0x100000000001e,
        'parent_file_reference': 0x5000000000005,
        'update_reason_flags': 0x00000100,
        'update_time': '2015-11-30T21:15:27.2031250+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
