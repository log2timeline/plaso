#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the NTFS metadata file parser."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.formatters import file_system  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import ntfs

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class NTFSMFTParserTest(test_lib.ParserTestCase):
  """Tests for NTFS $MFT metadata file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'MFT'])
  def testParseFile(self):
    """Tests the Parse function on a stand-alone $MFT file."""
    parser = ntfs.NTFSMFTParser()

    test_path = self._GetTestFilePath([u'MFT'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    storage_writer = self._ParseFileByPathSpec(os_path_spec, parser)

    self.assertEqual(storage_writer.number_of_events, 126352)

    events = list(storage_writer.GetEvents())

    # A distributed link tracking event.
    event = events[3684]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2007-06-30 12:58:40.500004')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'9fe44b69-2709-11dc-a06b-db3099beae3c '
        u'MAC address: db:30:99:be:ae:3c '
        u'Origin: $MFT: 462-1')

    expected_short_message = (
        u'9fe44b69-2709-11dc-a06b-db3099beae3c '
        u'Origin: $MFT: 462-1')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'vsstest.qcow2'])
  @shared_test_lib.skipUnlessHasTestFile([u'multi_partition_image.vmdk'])
  def testParseImage(self):
    """Tests the Parse function on a storage media image."""
    parser = ntfs.NTFSMFTParser()

    test_path = self._GetTestFilePath([u'vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=0, location=u'/$MFT',
        parent=qcow_path_spec)

    storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

    self.assertEqual(storage_writer.number_of_events, 284)

    events = list(storage_writer.GetEvents())

    # The creation timestamp.
    event = events[0]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    # The last modification timestamp.
    event = events[1]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    # The last accessed timestamp.
    event = events[2]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)
    self.assertEqual(event.timestamp, expected_timestamp)

    # The entry modification timestamp.
    event = events[3]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event.timestamp_desc,
        definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'TSK:/$MFT '
        u'File reference: 0-1 '
        u'Attribute name: $STANDARD_INFORMATION')

    expected_short_message = (
        u'/$MFT 0-1 $STANDARD_INFORMATION')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # The creation timestamp.
    event = events[4]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event.is_allocated, bool)
    self.assertTrue(event.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'TSK:/$MFT '
        u'File reference: 0-1 '
        u'Attribute name: $FILE_NAME '
        u'Name: $MFT '
        u'Parent file reference: 5-5')

    expected_short_message = (
        u'/$MFT 0-1 $FILE_NAME')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Note that the source file is a RAW (VMDK flat) image.
    test_path = self._GetTestFilePath([u'multi_partition_image.vmdk'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    p2_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p2',
        part_index=3, start_offset=0x00510000, parent=os_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=0, location=u'/$MFT',
        parent=p2_path_spec)

    storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

    self.assertEqual(storage_writer.number_of_events, 184)


class NTFSUsnJrnlParser(test_lib.ParserTestCase):
  """Tests for NTFS $UsnJrnl metadata file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'usnjrnl.qcow2'])
  def testParseImage(self):
    """Tests the Parse function on a storage media image."""
    parser = ntfs.NTFSUsnJrnlParser()

    test_path = self._GetTestFilePath([u'usnjrnl.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p1',
        part_index=2, start_offset=0x00007e00, parent=qcow_path_spec)

    # To be able to ignore the sparse data ranges the UsnJrnl parser
    # requires to read directly from the volume.
    storage_writer = self._ParseFileByPathSpec(volume_path_spec, parser)

    self.assertEqual(storage_writer.number_of_events, 19)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-11-30 21:15:27.203125')
    self.assertEqual(
        event.timestamp_desc,
        definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'Nieuw - Tekstdocument.txt '
        u'File reference: 30-1 '
        u'Parent file reference: 5-5 '
        u'Update reason: USN_REASON_FILE_CREATE')

    expected_short_message = (
        u'Nieuw - Tekstdocument.txt 30-1 USN_REASON_FILE_CREATE')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
