#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the NTFS metadata file parser."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import definitions
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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 126352)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # A distributed link tracking event.
    expected_event_values = {
        'data_type': 'windows:distributed_link_tracking:creation',
        'date_time': '2007-06-30 12:58:40.5000041',
        'mac_address': 'db:30:99:be:ae:3c',
        'origin': '$MFT: 462-1',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'uuid': '9fe44b69-2709-11dc-a06b-db3099beae3c'}

    self.CheckEventValues(storage_writer, events[3680], expected_event_values)

    # Test path hints of a regular file.
    expected_event_values = {
        'data_type': 'fs:stat:ntfs',
        'name': 'SAM',
        'path_hints': ['\\WINDOWS\\system32\\config\\SAM']}

    self.CheckEventValues(storage_writer, events[28741], expected_event_values)

    # Test path hints of a deleted file.
    expected_path_hints = [(
        '\\Documents and Settings\\Donald Blake\\Local Settings\\'
        'Temporary Internet Files\\Content.IE5\\9EUWFPZ1\\CAJA1S19.js')]

    expected_event_values = {
        'data_type': 'fs:stat:ntfs',
        'date_time': '2009-01-14 03:38:58.5869993',
        'is_allocated': False,
        'name': 'CAJA1S19.js',
        'path_hints': expected_path_hints}

    self.CheckEventValues(storage_writer, events[120476], expected_event_values)

    # Testing path hint of orphaned file.
    expected_event_values = {
        'data_type': 'fs:stat:ntfs',
        'date_time': '2009-01-14 21:07:11.5721856',
        'name': 'menu.text.css',
        'path_hints': ['$Orphan\\session\\menu.text.css']}

    self.CheckEventValues(storage_writer, events[125432], expected_event_values)

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 284)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # The creation timestamp.
    expected_event_values = {
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:30:41.8079077',
        'is_allocated': True,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # The last modification timestamp.
    expected_event_values = {
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:30:41.8079077',
        'is_allocated': True,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # The last accessed timestamp.
    expected_event_values = {
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:30:41.8079077',
        'is_allocated': True,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # The entry modification timestamp.
    expected_event_values = {
        'attribute_type': 0x00000010,
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:30:41.8079077',
        'display_name': 'TSK:/$MFT',
        'file_reference': 0x1000000000000,
        'is_allocated': True,
        'path_hints': ['\\$MFT'],
        'timestamp_desc': definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    # The creation timestamp.
    expected_event_values = {
        'attribute_type': 0x00000030,
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:30:41.8079077',
        'file_reference': 0x1000000000000,
        'is_allocated': True,
        'name': '$MFT',
        'parent_file_reference': 0x5000000000005,
        'path_hints': ['\\$MFT'],
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'attribute_type': 0x00000010,
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:35:09.5179783',
        'display_name': 'TSK:/$MFT',
        'file_reference': 0x1000000000026,
        'path_hints': [
            '\\System Volume Information\\{3808876b-c176-4e48-b7ae-'
            '04046e6cc752}']}

    self.CheckEventValues(storage_writer, events[251], expected_event_values)

    expected_event_values = {
        'attribute_type': 0x00000030,
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:35:09.5023783',
        'display_name': 'TSK:/$MFT',
        'file_reference': 0x1000000000026,
        'name': '{38088~1',
        'parent_file_reference': 0x1000000000024,
        'path_hints': ['\\System Volume Information\\{38088~1']}

    self.CheckEventValues(storage_writer, events[240], expected_event_values)

    expected_event_values = {
        'attribute_type': 0x00000030,
        'data_type': 'fs:stat:ntfs',
        'date_time': '2013-12-03 06:35:09.5023783',
        'display_name': 'TSK:/$MFT',
        'file_reference': 0x1000000000026,
        'name': '{3808876b-c176-4e48-b7ae-04046e6cc752}',
        'parent_file_reference': 0x1000000000024,
        'path_hints': [
            '\\System Volume Information\\'
            '{3808876b-c176-4e48-b7ae-04046e6cc752}']}

    self.CheckEventValues(storage_writer, events[244], expected_event_values)

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 184)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 19)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'fs:ntfs:usn_change',
        'date_time': '2015-11-30 21:15:27.2031250',
        'filename': 'Nieuw - Tekstdocument.txt',
        'file_reference': 0x100000000001e,
        'parent_file_reference': 0x5000000000005,
        'timestamp_desc': definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION,
        'update_reason_flags': 0x00000100}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
