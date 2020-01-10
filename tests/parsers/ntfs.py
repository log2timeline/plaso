#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the NTFS metadata file parser."""

from __future__ import unicode_literals

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.formatters import file_system  # pylint: disable=unused-import
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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 126352)

    events = list(storage_writer.GetEvents())

    # A distributed link tracking event.
    event = events[3680]

    self.CheckTimestamp(event.timestamp, '2007-06-30 12:58:40.500004')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '9fe44b69-2709-11dc-a06b-db3099beae3c '
        'MAC address: db:30:99:be:ae:3c '
        'Origin: $MFT: 462-1')

    expected_short_message = (
        '9fe44b69-2709-11dc-a06b-db3099beae3c '
        'Origin: $MFT: 462-1')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test path hints of a regular file.
    event = events[28741]
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.name, 'SAM')

    expected_path_hints = ['\\WINDOWS\\system32\\config\\SAM']
    self.assertEqual(event_data.path_hints, expected_path_hints)

    # Test path hints of a deleted file.
    event = events[120476]
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.name, 'CAJA1S19.js')
    self.assertFalse(event_data.is_allocated)

    expected_path_hints = [(
        '\\Documents and Settings\\Donald Blake\\Local Settings\\'
        'Temporary Internet Files\\Content.IE5\\9EUWFPZ1\\CAJA1S19.js')]
    self.assertEqual(event_data.path_hints, expected_path_hints)

    # Testing path hint of orphaned file.
    event = events[125432]
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.name, 'menu.text.css')

    expected_path_hints = ['$Orphan\\session\\menu.text.css']
    self.assertEqual(event_data.path_hints, expected_path_hints)

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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 284)

    events = list(storage_writer.GetEvents())

    # The creation timestamp.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_data.is_allocated, bool)
    self.assertTrue(event_data.is_allocated)

    # The last modification timestamp.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_data.is_allocated, bool)
    self.assertTrue(event_data.is_allocated)

    # The last accessed timestamp.
    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_data.is_allocated, bool)
    self.assertTrue(event_data.is_allocated)

    # The entry modification timestamp.
    event = events[7]

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_data.is_allocated, bool)
    self.assertTrue(event_data.is_allocated)

    expected_message = (
        'TSK:/$MFT '
        'File reference: 0-1 '
        'Attribute name: $STANDARD_INFORMATION '
        'Path hints: \\$MFT')

    expected_short_message = (
        '/$MFT 0-1 $STANDARD_INFORMATION')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # The creation timestamp.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_data.is_allocated, bool)
    self.assertTrue(event_data.is_allocated)

    expected_message = (
        'TSK:/$MFT '
        'File reference: 0-1 '
        'Attribute name: $FILE_NAME '
        'Name: $MFT '
        'Parent file reference: 5-5 '
        'Path hints: \\$MFT')

    expected_short_message = (
        '/$MFT 0-1 $FILE_NAME')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[251]
    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_path_hints = [
        '\\System Volume Information\\{3808876b-c176-4e48-b7ae-04046e6cc752}']

    self.assertEqual(event_data.path_hints, expected_path_hints)

    expected_message = (
        'TSK:/$MFT '
        'File reference: 38-1 '
        'Attribute name: $STANDARD_INFORMATION '
        'Path hints: \\System Volume Information\\'
        '{3808876b-c176-4e48-b7ae-04046e6cc752}')

    expected_short_message = (
        '/$MFT 38-1 $STANDARD_INFORMATION')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[240]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_path_hints = ['\\System Volume Information\\{38088~1']
    self.assertEqual(event_data.path_hints, expected_path_hints)

    expected_message = (
        'TSK:/$MFT '
        'File reference: 38-1 '
        'Attribute name: $FILE_NAME '
        'Name: {38088~1 '
        'Parent file reference: 36-1 '
        'Path hints: \\System Volume Information\\{38088~1')

    expected_short_message = (
        '/$MFT 38-1 $FILE_NAME')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[244]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_path_hints = [
        '\\System Volume Information\\{3808876b-c176-4e48-b7ae-04046e6cc752}']
    self.assertEqual(event_data.path_hints, expected_path_hints)

    expected_message = (
        'TSK:/$MFT '
        'File reference: 38-1 '
        'Attribute name: $FILE_NAME '
        'Name: {3808876b-c176-4e48-b7ae-04046e6cc752} '
        'Parent file reference: 36-1 '
        'Path hints: \\System Volume Information\\'
        '{3808876b-c176-4e48-b7ae-04046e6cc752}')

    expected_short_message = (
        '/$MFT 38-1 $FILE_NAME')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 184)


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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 19)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2015-11-30 21:15:27.203125')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Nieuw - Tekstdocument.txt '
        'File reference: 30-1 '
        'Parent file reference: 5-5 '
        'Update reason: USN_REASON_FILE_CREATE')

    expected_short_message = (
        'Nieuw - Tekstdocument.txt 30-1 USN_REASON_FILE_CREATE')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
