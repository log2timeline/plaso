#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Drive Sync log log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import gdrive_synclog as _  # pylint: disable=unused-import
from plaso.parsers import gdrive_synclog

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class GoogleDriveSyncLogUnitTest(test_lib.ParserTestCase):
  """Tests for the Google Drive Sync log parser."""

  @shared_test_lib.skipUnlessHasTestFile(['sync_log.log'])
  def testParseLog(self):
    """Tests the Parse function on normal log."""
    parser = gdrive_synclog.GoogleDriveSyncLogParser()
    storage_writer = self._ParseFile(['sync_log.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 2190)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:08.454000')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:08.454000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:08.456000')

    expected_message = (
        '[INFO pid=2376 7780:MainThread logging_config.py:299]  SSL: OpenSSL '
        '1.0.2m  2 Nov 2017')
    expected_short_message = (
        ' SSL: OpenSSL 1.0.2m  2 Nov 2017')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[30]
    expected_message = (
        '[INFO pid=2376 6560:RunAsync-_InitializeSyncAppAsync-1 persistence.'
        'py:38]  Initialize factory with policy PlatformPolicy('
        'google_drive_config_directory_path=u\'C:\\\\Users\\\\John\\\\App'
        'Data\\\\Local\\\\Google\\\\Drive\', main_sync_root=None, '
        'profile_id=None)')
    expected_short_message = (
        ' Initialize factory with policy '
        'PlatformPolicy(google_drive_config_directory_...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[82]

    self.CheckTimestamp(event.timestamp, '2018-01-25 02:25:18.563000')

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
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
