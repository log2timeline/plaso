#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Dropbox sync_history database plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import dropbox

from tests.parsers.sqlite_plugins import test_lib


class DropboxSyncHistoryPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Dropbox sync_history database plugin."""

  def testProcess(self):
    """Tests the Process function on a Dropbox sync_history database file."""
    plugin = dropbox.DropboxSyncDatabasePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['sync_history.db'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'event_type': 'file',
        'file_event_type': 'add',
        'direction': 'upload',
        'file_identifier': 'XXXXXXXXXXXAAAAAAAAAGg',
        'local_path': '/home/useraa/Dropbox/loc1/create_local.txt',
        'date_time': '2022-02-17 10:57:18',
        'timestamp_desc': definitions.TIME_DESCRIPTION_RECORDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'event_type': 'file',
        'file_event_type': 'delete',
        'direction': 'upload',
        'file_identifier': 'XXXXXXXXXXXAAAAAAAAAKg',
        'local_path': '/home/useraa/Dropbox/loc1/.create_local.txt.swp',
        'date_time': '2022-02-17 10:57:19',
        'timestamp_desc': definitions.TIME_DESCRIPTION_RECORDED}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'event_type': 'file',
        'file_event_type': 'add',
        'direction': 'download',
        'file_identifier': 'XXXXXXXXXXXAAAAAAAAAKw',
        'local_path': '/home/useraa/Dropbox/web1/create_web.txt',
        'date_time': '2022-02-17 11:01:21',
        'timestamp_desc': definitions.TIME_DESCRIPTION_RECORDED}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'event_type': 'file',
        'file_event_type': 'delete',
        'direction': 'download',
        'file_identifier': 'XXXXXXXXXXXAAAAAAAAALA',
        'local_path': '/home/useraa/Dropbox/web2/create_web.txt',
        'date_time': '2022-02-17 11:04:03',
        'timestamp_desc': definitions.TIME_DESCRIPTION_RECORDED}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'event_type': 'file',
        'file_event_type': 'edit',
        'direction': 'download',
        'file_identifier': 'XXXXXXXXXXXAAAAAAAAALQ',
        'local_path': '/home/useraa/Dropbox/web2/Document.docx',
        'date_time': '2022-02-17 11:05:50',
        'timestamp_desc': definitions.TIME_DESCRIPTION_RECORDED}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'event_type': 'file',
        'file_event_type': 'add',
        'direction': 'download',
        'file_identifier': 'XXXXXXXXXXXAAAAAAAAALg',
        'local_path': '/home/useraa/Dropbox/web2/Untitled.gdoc',
        'date_time': '2022-02-17 11:06:34',
        'timestamp_desc': definitions.TIME_DESCRIPTION_RECORDED}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)


if __name__ == '__main__':
  unittest.main()
