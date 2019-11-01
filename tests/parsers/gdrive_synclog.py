#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Drive Sync log log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import gdrive_synclog as _  # pylint: disable=unused-import
from plaso.parsers import gdrive_synclog

from tests.parsers import test_lib


class GoogleDriveSyncLogUnitTest(test_lib.ParserTestCase):
  """Tests for the Google Drive Sync log parser."""

  def testParseLog(self):
    """Tests the Parse function on normal log."""
    parser = gdrive_synclog.GoogleDriveSyncLogParser()
    storage_writer = self._ParseFile(['sync_log.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2190)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:08.454000')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:08.454000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:08.456000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[INFO pid=2376 7780:MainThread logging_config.py:299]  SSL: OpenSSL '
        '1.0.2m  2 Nov 2017')
    expected_short_message = (
        ' SSL: OpenSSL 1.0.2m  2 Nov 2017')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[30]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[INFO pid=2376 6560:RunAsync-_InitializeSyncAppAsync-1 persistence.'
        'py:38]  Initialize factory with policy PlatformPolicy('
        'google_drive_config_directory_path=u\'C:\\\\Users\\\\John\\\\App'
        'Data\\\\Local\\\\Google\\\\Drive\', main_sync_root=None, '
        'profile_id=None)')
    expected_short_message = (
        ' Initialize factory with policy '
        'PlatformPolicy(google_drive_config_directory_...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[82]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:18.563000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[INFO pid=2376 5712:ExternalBrowserFlow proxy_manager.py:141]  '
        'Exception while auto resolving proxy. Traceback (most recent call '
        'last):   File "common\\proxy_manager.py", line 135, in '
        '_GetProxyInfoForUrl   File "windows\\system_proxy_resolver.py", '
        'line 96, in GetProxyForUrlViaWPAD   File '
        '"windows\\system_proxy_resolver.py", line 155, in _GetProxy '
        'ProxyInfoResolutionError: ProxyInfoResolutionError: inner_error=('
        '12180, \'WinHttpGetProxyForUrl\', \'The Proxy Auto-configuration URL '
        'was not found.\')')
    expected_short_message = (
        ' Exception while auto resolving proxy. Traceback (most recent call '
        'last):   F...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testOSXParseLog(self):
    """Tests the Parse function on OS X log.

    Test contains UTC timestamps and Unicode (UTF-8) filenames.
    """
    parser = gdrive_synclog.GoogleDriveSyncLogParser()
    storage_writer = self._ParseFile(['sync_log-osx.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2338)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2018-03-01 20:48:14.224000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[INFO pid=1730 140736280556352:MainThread logging_config.pyo:295]  '
        'OS: Darwin/10.13.3')
    expected_short_message = ' OS: Darwin/10.13.3'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Log file contains a change in local system time from -0800 to UTC, around
    # line 215. Confirm the switch is handled correctly.
    event = events[169]

    self.CheckTimestamp(event.timestamp, '2018-03-01 20:57:33.499000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[INFO pid=2590 140736280556352:MainThread logging_config.pyo:299]  SSL'
        ': OpenSSL 1.0.2n  7 Dec 2017')
    expected_short_message = ' SSL: OpenSSL 1.0.2n  7 Dec 2017'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Ensure Unicode characters in filenames are handled cleanly.
    event = events[1400]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        '[INFO pid=2608 123145558327296:Worker-1 snapshot_sqlite.pyo:219]  '
        'Updating local entry local_id=LocalID(inode=870321, volume=\'60228'
        'B87-A626-4F5C-873E-476615F863C6\'), filename=АБВГДЕ.gdoc, modified'
        '=1520218963, checksum=ab0618852c5d671d7b1b9191aef03bda, size=185, '
        'is_folder=False')
    expected_short_message = (
        ' Updating local entry local_id=LocalID(inode=870321, '
        'volume=\'60228B87-A626-4F...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
