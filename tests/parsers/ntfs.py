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

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class NTFSMFTParserTest(test_lib.ParserTestCase):
  """Tests for NTFS $MFT metadata file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['MFT'])
  def testParseFile(self):
    """Tests the Parse function on a stand-alone $MFT file."""
    parser = ntfs.NTFSMFTParser()

    test_path = self._GetTestFilePath(['MFT'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    storage_writer = self._ParseFileByPathSpec(os_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 126352)

    events = list(storage_writer.GetEvents())

    # A distributed link tracking event.
    event = events[3684]

    self.CheckTimestamp(event.timestamp, '2007-06-30 12:58:40.500004')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_message = (
        '9fe44b69-2709-11dc-a06b-db3099beae3c '
        'MAC address: db:30:99:be:ae:3c '
        'Origin: $MFT: 462-1')

    expected_short_message = (
        '9fe44b69-2709-11dc-a06b-db3099beae3c '
        'Origin: $MFT: 462-1')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['vsstest.qcow2'])
  @shared_test_lib.skipUnlessHasTestFile(['multi_partition_image.vmdk'])
  def testParseImage(self):
    """Tests the Parse function on a storage media image."""
    parser = ntfs.NTFSMFTParser()

    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
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

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    # The last modification timestamp.
    event = events[1]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    # The last accessed timestamp.
    event = events[2]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    # The entry modification timestamp.
    event = events[3]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)

    expected_message = (
        'TSK:/$MFT '
        'File reference: 0-1 '
        'Attribute name: $STANDARD_INFORMATION')

    expected_short_message = (
        '/$MFT 0-1 $STANDARD_INFORMATION')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The creation timestamp.
    event = events[4]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    self.CheckTimestamp(event.timestamp, '2013-12-03 06:30:41.807908')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    expected_message = (
        'TSK:/$MFT '
        'File reference: 0-1 '
        'Attribute name: $FILE_NAME '
        'Name: $MFT '
        'Parent file reference: 5-5')

    expected_short_message = (
        '/$MFT 0-1 $FILE_NAME')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Note that the source file is a RAW (VMDK flat) image.
    test_path = self._GetTestFilePath(['multi_partition_image.vmdk'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
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

  @shared_test_lib.skipUnlessHasTestFile(['usnjrnl.qcow2'])
  def testParseImage(self):
    """Tests the Parse function on a storage media image."""
    parser = ntfs.NTFSUsnJrnlParser()

    test_path = self._GetTestFilePath(['usnjrnl.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
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

    expected_message = (
        'Nieuw - Tekstdocument.txt '
        'File reference: 30-1 '
        'Parent file reference: 5-5 '
        'Update reason: USN_REASON_FILE_CREATE')

    expected_short_message = (
        'Nieuw - Tekstdocument.txt 30-1 USN_REASON_FILE_CREATE')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
