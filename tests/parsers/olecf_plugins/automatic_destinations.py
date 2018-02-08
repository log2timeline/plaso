#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the .automaticDestinations-ms OLECF parser plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import olecf  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.olecf_plugins import automatic_destinations

from tests import test_lib as shared_test_lib
from tests.parsers.olecf_plugins import test_lib


class TestAutomaticDestinationsOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the .automaticDestinations-ms OLECF parser plugin."""

  @shared_test_lib.skipUnlessHasTestFile([
      '1b4dd67f29cb1962.automaticDestinations-ms'])
  def testProcessVersion1(self):
    """Tests the Process function on version 1 .automaticDestinations-ms."""
    plugin = automatic_destinations.AutomaticDestinationsOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        ['1b4dd67f29cb1962.automaticDestinations-ms'], plugin)

    self.assertEqual(storage_writer.number_of_events, 88)

    events = list(storage_writer.GetEvents())

    # Check a AutomaticDestinationsDestListEntryEvent.
    event = events[7]

    self.assertEqual(event.offset, 32)
    self.assertEqual(event.data_type, 'olecf:dest_list:entry')

    self.CheckTimestamp(event.timestamp, '2012-04-01 13:52:38.997538')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    expected_message = (
        'Entry: 11 '
        'Pin status: Unpinned '
        'Hostname: wks-win764bitb '
        'Path: C:\\Users\\nfury\\Pictures\\The SHIELD '
        'Droid volume identifier: {cf6619c2-66a8-44a6-8849-1582fcd3a338} '
        'Droid file identifier: {63eea867-7b85-11e1-8950-005056a50b40} '
        'Birth droid volume identifier: '
        '{cf6619c2-66a8-44a6-8849-1582fcd3a338} '
        'Birth droid file identifier: {63eea867-7b85-11e1-8950-005056a50b40}')

    expected_short_message = (
        'Entry: 11 '
        'Pin status: Unpinned '
        'Path: C:\\Users\\nfury\\Pictures\\The SHIELD')

    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

    # Check a WinLnkLinkEvent.
    event = events[1]

    self.assertEqual(event.data_type, 'windows:lnk:link')

    self.CheckTimestamp(event.timestamp, '2010-11-10 07:51:16.749125')

    expected_message = (
        '[Empty description] '
        'File size: 3545 '
        'File attribute flags: 0x00002020 '
        'Drive type: 3 '
        'Drive serial number: 0x24ba718b '
        'Local path: C:\\Users\\nfury\\AppData\\Roaming\\Microsoft\\Windows\\'
        'Libraries\\Documents.library-ms '
        'Link target: <Users Libraries> <UNKNOWN: 0x00>')

    expected_short_message = (
        '[Empty description] '
        'C:\\Users\\nfury\\AppData\\Roaming\\Microsoft\\Windows\\Librarie...')

    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

    # Check a WindowsDistributedLinkTrackingCreationEvent.
    event = events[5]

    self.assertEqual(
        event.data_type, 'windows:distributed_link_tracking:creation')

    self.CheckTimestamp(event.timestamp, '2012-03-31 23:01:03.527741')

    expected_message = (
        '63eea867-7b85-11e1-8950-005056a50b40 '
        'MAC address: 00:50:56:a5:0b:40 '
        'Origin: DestList entry at offset: 0x00000020')

    expected_short_message = (
        '63eea867-7b85-11e1-8950-005056a50b40 '
        'Origin: DestList entry at offset: 0x0000...')

    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([
      '9d1f905ce5044aee.automaticDestinations-ms'])
  def testProcessVersion3(self):
    """Tests the Process function on version 3 .automaticDestinations-ms."""
    plugin = automatic_destinations.AutomaticDestinationsOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        ['9d1f905ce5044aee.automaticDestinations-ms'], plugin)

    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    # Check a AutomaticDestinationsDestListEntryEvent.

    # Check a WinLnkLinkEvent.
    event = events[1]

    self.assertEqual(event.offset, 32)
    self.assertEqual(event.data_type, 'olecf:dest_list:entry')

    self.CheckTimestamp(event.timestamp, '2016-01-17 13:08:08.247504')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    expected_message = (
        'Entry: 2 '
        'Pin status: Unpinned '
        'Path: http://support.microsoft.com/kb/3124263 '
        'Droid volume identifier: {00000000-0000-0000-0000-000000000000} '
        'Droid file identifier: {00000000-0000-0000-0000-000000000000} '
        'Birth droid volume identifier: '
        '{00000000-0000-0000-0000-000000000000} '
        'Birth droid file identifier: {00000000-0000-0000-0000-000000000000}')

    expected_short_message = (
        'Entry: 2 '
        'Pin status: Unpinned '
        'Path: http://support.microsoft.com/kb/3124263')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check a WinLnkLinkEvent.
    event = events[0]

    self.assertEqual(event.data_type, 'windows:lnk:link')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_NOT_A_TIME)


if __name__ == '__main__':
  unittest.main()
