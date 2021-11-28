#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Drive Sync log log parser."""

import unittest

from plaso.parsers import gdrive_synclog

from tests.parsers import test_lib


class GoogleDriveSyncLogUnitTest(test_lib.ParserTestCase):
  """Tests for the Google Drive Sync log parser."""

  def testParseLog(self):
    """Tests the Parse function on normal log."""
    parser = gdrive_synclog.GoogleDriveSyncLogParser()
    storage_writer = self._ParseFile(['sync_log.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2190)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-01-24 18:25:08.454',
        'timestamp': '2018-01-25 02:25:08.454000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-01-24 18:25:08.454',
        'timestamp': '2018-01-25 02:25:08.454000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-01-24 18:25:08.456',
        'log_level': 'INFO',
        'message': 'SSL: OpenSSL 1.0.2m  2 Nov 2017',
        'pid': 'pid=2376',
        'source_code': 'logging_config.py:299',
        'thread': '7780:MainThread',
        'timestamp': '2018-01-25 02:25:08.456000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # TODO: change parser to remove leading space from message value.
    # TODO: change parser to remove pid= from pid value.
    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-01-24 18:25:09.453',
        'log_level': 'INFO',
        'message': (
            'Initialize factory with policy PlatformPolicy('
            'google_drive_config_directory_path=u\'C:\\\\Users\\\\John\\\\App'
            'Data\\\\Local\\\\Google\\\\Drive\', main_sync_root=None, '
            'profile_id=None)'),
        'pid': 'pid=2376',
        'source_code': 'persistence.py:38',
        'thread': '6560:RunAsync-_InitializeSyncAppAsync-1',
        'timestamp': '2018-01-25 02:25:09.453000'}

    self.CheckEventValues(storage_writer, events[30], expected_event_values)

    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-01-24 18:25:18.563',
        'log_level': 'INFO',
        'message': (
            'Exception while auto resolving proxy. Traceback (most recent '
            'call last):   File "common\\proxy_manager.py", line 135, in '
            '_GetProxyInfoForUrl   File "windows\\system_proxy_resolver.py", '
            'line 96, in GetProxyForUrlViaWPAD   File "windows\\'
            'system_proxy_resolver.py", line 155, in _GetProxy '
            'ProxyInfoResolutionError: ProxyInfoResolutionError: inner_error=('
            '12180, \'WinHttpGetProxyForUrl\', \'The Proxy Auto-configuration '
            'URL was not found.\')'),
        'pid': 'pid=2376',
        'source_code': 'proxy_manager.py:141',
        'thread': '5712:ExternalBrowserFlow',
        'timestamp': '2018-01-25 02:25:18.563000'}

    self.CheckEventValues(storage_writer, events[82], expected_event_values)

  def testMacOSParseLog(self):
    """Tests the Parse function on Mac OS log.

    Test contains UTC timestamps and Unicode (UTF-8) filenames.
    """
    parser = gdrive_synclog.GoogleDriveSyncLogParser()
    storage_writer = self._ParseFile(['sync_log-osx.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2338)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-03-01 12:48:14.224',
        'log_level': 'INFO',
        'message': 'OS: Darwin/10.13.3',
        'pid': 'pid=1730',
        'source_code': 'logging_config.pyo:295',
        'thread': '140736280556352:MainThread',
        'timestamp': '2018-03-01 20:48:14.224000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Log file contains a change in local system time from -0800 to UTC, around
    # line 215. Confirm the switch is handled correctly.
    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-03-01 20:57:33.499',
        'log_level': 'INFO',
        'message': 'SSL: OpenSSL 1.0.2n  7 Dec 2017',
        'pid': 'pid=2590',
        'source_code': 'logging_config.pyo:299',
        'thread': '140736280556352:MainThread'}

    self.CheckEventValues(storage_writer, events[169], expected_event_values)

    # Ensure Unicode characters in filenames are handled cleanly.
    expected_event_values = {
        'data_type': 'gdrive_sync:log:line',
        'date_time': '2018-03-05 03:09:15.806',
        'log_level': 'INFO',
        'message': (
            'Updating local entry local_id=LocalID(inode=870321, volume='
            '\'60228B87-A626-4F5C-873E-476615F863C6\'), filename=АБВГДЕ.gdoc, '
            'modified=1520218963, checksum=ab0618852c5d671d7b1b9191aef03bda, '
            'size=185, is_folder=False'),
        'pid': 'pid=2608',
        'source_code': 'snapshot_sqlite.pyo:219',
        'thread': '123145558327296:Worker-1'}

    self.CheckEventValues(storage_writer, events[1400], expected_event_values)


if __name__ == '__main__':
  unittest.main()
