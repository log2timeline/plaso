#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for filestat parser."""

from __future__ import unicode_literals

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.formatters import file_system  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import filestat

from tests.parsers import test_lib


class FileStatTest(test_lib.ParserTestCase):
  """Tests for filestat parser."""

  def testTSKFile(self):
    """Read a file within an image file and make few tests."""
    parser = filestat.FileStatParser()

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
        location='/passwords.txt', parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-05-25 16:00:53.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.file_size, 116)
    self.assertEqual(event_data.inode, 15)
    self.assertEqual(event_data.file_system_type, 'EXT2')

    expected_message = (
        'TSK:/passwords.txt '
        'Type: file')
    expected_short_message = '/passwords.txt'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testZipFile(self):
    """Test a ZIP file."""
    parser = filestat.FileStatParser()

    test_file_path = self._GetTestFilePath(['syslog.zip'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_ZIP, location='/syslog',
        parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(zip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-07-24 14:45:24.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.file_size, 1247)
    self.assertIsNone(event_data.inode)

    expected_message = (
        'ZIP:/syslog '
        'Type: file')
    expected_short_message = '/syslog'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testGzipFile(self):
    """Test a GZIP file."""
    parser = filestat.FileStatParser()

    test_file_path = self._GetTestFilePath(['syslog.gz'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-07-28 16:44:07.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.file_size, 1247)
    self.assertIsNone(event_data.inode)

    test_path = os.path.join(os.getcwd(), 'test_data', 'syslog.gz')
    expected_message = (
        'GZIP:{0:s} '
        'Type: file').format(test_path)
    expected_short_message = self._GetShortMessage(test_path)
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testTarFile(self):
    """Test a TAR file."""
    parser = filestat.FileStatParser()

    test_file_path = self._GetTestFilePath(['syslog.tar'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location='/syslog',
        parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(tar_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-07-24 21:45:24.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.file_size, 1247)
    self.assertIsNone(event_data.inode)

    expected_message = (
        'TAR:/syslog '
        'Type: file')
    expected_short_message = '/syslog'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testNestedFile(self):
    """Test a nested file."""
    parser = filestat.FileStatParser()

    test_file_path = self._GetTestFilePath(['syslog.tgz'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location='/syslog',
        parent=gzip_path_spec)

    storage_writer = self._ParseFileByPathSpec(tar_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-07-24 21:45:24.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.file_size, 1247)
    self.assertIsNone(event_data.inode)

    expected_message = (
        'TAR:/syslog '
        'Type: file')
    expected_short_message = '/syslog'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    test_file_path = self._GetTestFilePath(['syslog.tgz'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-07-28 16:44:43.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.file_size, 10240)
    self.assertIsNone(event_data.inode)

    test_path = os.path.join(os.getcwd(), 'test_data', 'syslog.tgz')
    expected_message = (
        'GZIP:{0:s} '
        'Type: file').format(test_path)
    expected_short_message = self._GetShortMessage(test_path)
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testNestedTSK(self):
    """Test a nested TSK file."""
    parser = filestat.FileStatParser()

    test_file_path = self._GetTestFilePath(['syslog_image.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=11,
        location='/logs/hidden.zip', parent=os_path_spec)
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_ZIP, location='/syslog',
        parent=tsk_path_spec)

    storage_writer = self._ParseFileByPathSpec(zip_path_spec, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-07-20 15:44:14.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.file_size, 1247)
    self.assertIsNone(event_data.inode)

    expected_message = (
        'ZIP:/syslog '
        'Type: file')
    expected_short_message = '/syslog'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
