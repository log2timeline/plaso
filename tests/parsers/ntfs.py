#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the NTFS metadata file parser."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

# pylint: disable=unused-import
from plaso.formatters import file_system as file_system_formatter
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import ntfs

from tests.parsers import test_lib


class NTFSMFTParserTest(test_lib.ParserTestCase):
  """Tests for NTFS $MFT metadata file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = ntfs.NTFSMFTParser()

  def testParseFile(self):
    """Tests the Parse function on a stand-alone $MFT file."""
    test_path = self._GetTestFilePath([u'MFT'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, os_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 126352)

    # A distributed link tracking event.
    event_object = event_objects[3684]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2007-06-30 12:58:40.500004')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'9fe44b69-2709-11dc-a06b-db3099beae3c '
        u'MAC address: db:30:99:be:ae:3c '
        u'Origin: $MFT: 462-1')

    expected_short_message = (
        u'9fe44b69-2709-11dc-a06b-db3099beae3c '
        u'Origin: $MFT: 462-1')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testParseImage(self):
    """Tests the Parse function on a storage media image."""
    test_path = self._GetTestFilePath([u'vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=0, location=u'/$MFT',
        parent=qcow_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, tsk_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 284)

    # The creation timestamp.
    event_object = event_objects[0]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_object.is_allocated, bool)
    self.assertTrue(event_object.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The last modification timestamp.
    event_object = event_objects[1]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_object.is_allocated, bool)
    self.assertTrue(event_object.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The last accessed timestamp.
    event_object = event_objects[2]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_object.is_allocated, bool)
    self.assertTrue(event_object.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The entry modification timestamp.
    event_object = event_objects[3]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_object.is_allocated, bool)
    self.assertTrue(event_object.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.ENTRY_MODIFICATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'TSK:/$MFT '
        u'File reference: 0-1 '
        u'Attribute name: $STANDARD_INFORMATION')

    expected_short_message = (
        u'/$MFT 0-1 $STANDARD_INFORMATION')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    # The creation timestamp.
    event_object = event_objects[4]

    # Check that the allocation status is set correctly.
    self.assertIsInstance(event_object.is_allocated, bool)
    self.assertTrue(event_object.is_allocated)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-03 06:30:41.807907')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'TSK:/$MFT '
        u'File reference: 0-1 '
        u'Attribute name: $FILE_NAME '
        u'Name: $MFT '
        u'Parent file reference: 5-5')

    expected_short_message = (
        u'/$MFT 0-1 $FILE_NAME')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

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

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, tsk_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 184)


if __name__ == '__main__':
  unittest.main()
