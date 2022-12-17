#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Drive Sync log log text parser plugin."""

import unittest

from dfvfs.helpers import fake_file_system_builder

from plaso.parsers import text_parser
from plaso.parsers.text_plugins import gdrive_synclog

from tests.parsers.text_plugins import test_lib


class GoogleDriveSyncLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Google Drive Sync log text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = gdrive_synclog.GoogleDriveSyncLogTextPlugin()

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/file.txt', (
        b'2018-01-24 18:25:08,454 -0800 INFO pid=2376 7780:MainThread      '
        b'logging_config.py:295 OS: Windows/6.1-SP1\n'))

    file_entry = file_system_builder.file_system.GetFileEntryByPath('/file.txt')

    parser_mediator = self._CreateParserMediator(None, file_entry=file_entry)

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    result = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(result)

  def testProcess(self):
    """Tests the Process function."""
    plugin = gdrive_synclog.GoogleDriveSyncLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['sync_log.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2190)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2018-01-24T18:25:08.456-08:00',
        'data_type': 'google_drive_sync_log:entry',
        'level': 'INFO',
        'message': 'SSL: OpenSSL 1.0.2m  2 Nov 2017',
        'process_identifier': 2376,
        'source_code': 'logging_config.py:299',
        'thread': '7780:MainThread'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithMacOSLog(self):
    """Tests the Process function with a MacOS Google Drive sync log."""
    plugin = gdrive_synclog.GoogleDriveSyncLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['sync_log-osx.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2338)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2018-03-01T12:48:14.224-08:00',
        'data_type': 'google_drive_sync_log:entry',
        'level': 'INFO',
        'message': 'OS: Darwin/10.13.3',
        'process_identifier': 1730,
        'source_code': 'logging_config.pyo:295',
        'thread': '140736280556352:MainThread'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test change in local system time from -0800 to UTC.
    # The switch occurs around line 215.
    expected_event_values = {
        'added_time': '2018-03-01T20:57:33.499+00:00',
        'data_type': 'google_drive_sync_log:entry',
        'level': 'INFO',
        'message': 'SSL: OpenSSL 1.0.2n  7 Dec 2017',
        'process_identifier': 2590,
        'source_code': 'logging_config.pyo:299',
        'thread': '140736280556352:MainThread'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 169)
    self.CheckEventData(event_data, expected_event_values)

    # Test with Unicode characters in filename.
    expected_event_values = {
        'added_time': '2018-03-05T03:09:15.806+00:00',
        'data_type': 'google_drive_sync_log:entry',
        'level': 'INFO',
        'message': (
            'Updating local entry local_id=LocalID(inode=870321, volume='
            '\'60228B87-A626-4F5C-873E-476615F863C6\'), filename=АБВГДЕ.gdoc, '
            'modified=1520218963, checksum=ab0618852c5d671d7b1b9191aef03bda, '
            'size=185, is_folder=False'),
        'process_identifier': 2608,
        'source_code': 'snapshot_sqlite.pyo:219',
        'thread': '123145558327296:Worker-1'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1400)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
