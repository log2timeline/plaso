#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the .automaticDestinations-ms OLECF parser plugin."""

import unittest

from plaso.formatters import olecf  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.olecf_plugins import automatic_destinations

from tests import test_lib as shared_test_lib
from tests.parsers.olecf_plugins import test_lib


class TestAutomaticDestinationsOLECFPlugin(test_lib.OLECFPluginTestCase):
  """Tests for the .automaticDestinations-ms OLECF parser plugin."""

  @shared_test_lib.skipUnlessHasTestFile([
      u'1b4dd67f29cb1962.automaticDestinations-ms'])
  def testProcessVersion1(self):
    """Tests the Process function on version 1 .automaticDestinations-ms."""
    plugin_object = automatic_destinations.AutomaticDestinationsOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        [u'1b4dd67f29cb1962.automaticDestinations-ms'], plugin_object)

    self.assertEqual(len(storage_writer.events), 88)

    # Check a AutomaticDestinationsDestListEntryEvent.
    event_object = storage_writer.events[7]

    self.assertEqual(event_object.offset, 32)
    self.assertEqual(event_object.data_type, u'olecf:dest_list:entry')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-01 13:52:38.997538')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'Entry: 11 '
        u'Pin status: Unpinned '
        u'Hostname: wks-win764bitb '
        u'Path: C:\\Users\\nfury\\Pictures\\The SHIELD '
        u'Droid volume identifier: {cf6619c2-66a8-44a6-8849-1582fcd3a338} '
        u'Droid file identifier: {63eea867-7b85-11e1-8950-005056a50b40} '
        u'Birth droid volume identifier: '
        u'{cf6619c2-66a8-44a6-8849-1582fcd3a338} '
        u'Birth droid file identifier: {63eea867-7b85-11e1-8950-005056a50b40}')

    expected_message_short = (
        u'Entry: 11 '
        u'Pin status: Unpinned '
        u'Path: C:\\Users\\nfury\\Pictures\\The SHIELD')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

    # Check a WinLnkLinkEvent.
    event_object = storage_writer.events[1]

    self.assertEqual(event_object.data_type, u'windows:lnk:link')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:51:16.749125')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[Empty description] '
        u'File size: 3545 '
        u'File attribute flags: 0x00002020 '
        u'Drive type: 3 '
        u'Drive serial number: 0x24ba718b '
        u'Local path: C:\\Users\\nfury\\AppData\\Roaming\\Microsoft\\Windows\\'
        u'Libraries\\Documents.library-ms '
        u'Link target: <Users Libraries> <UNKNOWN: 0x00>')

    expected_message_short = (
        u'[Empty description] '
        u'C:\\Users\\nfury\\AppData\\Roaming\\Microsoft\\Windows\\Librarie...')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

    # Check a WindowsDistributedLinkTrackingCreationEvent.
    event_object = storage_writer.events[5]

    self.assertEqual(
        event_object.data_type, u'windows:distributed_link_tracking:creation')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-31 23:01:03.527741')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'63eea867-7b85-11e1-8950-005056a50b40 '
        u'MAC address: 00:50:56:a5:0b:40 '
        u'Origin: DestList entry at offset: 0x00000020')

    expected_message_short = (
        u'63eea867-7b85-11e1-8950-005056a50b40 '
        u'Origin: DestList entry at offset: 0x0000...')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

  @shared_test_lib.skipUnlessHasTestFile([
      u'9d1f905ce5044aee.automaticDestinations-ms'])
  def testProcessVersion3(self):
    """Tests the Process function on version 3 .automaticDestinations-ms."""
    plugin_object = automatic_destinations.AutomaticDestinationsOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(
        [u'9d1f905ce5044aee.automaticDestinations-ms'], plugin_object)

    self.assertEqual(len(storage_writer.events), 4)

    # Check a AutomaticDestinationsDestListEntryEvent.

    # Check a WinLnkLinkEvent.
    event_object = storage_writer.events[1]

    self.assertEqual(event_object.offset, 32)
    self.assertEqual(event_object.data_type, u'olecf:dest_list:entry')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-01-17 13:08:08.247504')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'Entry: 2 '
        u'Pin status: Unpinned '
        u'Path: http://support.microsoft.com/kb/3124263 '
        u'Droid volume identifier: {00000000-0000-0000-0000-000000000000} '
        u'Droid file identifier: {00000000-0000-0000-0000-000000000000} '
        u'Birth droid volume identifier: '
        u'{00000000-0000-0000-0000-000000000000} '
        u'Birth droid file identifier: {00000000-0000-0000-0000-000000000000}')

    expected_message_short = (
        u'Entry: 2 '
        u'Pin status: Unpinned '
        u'Path: http://support.microsoft.com/kb/3124263')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

    # Check a WinLnkLinkEvent.
    event_object = storage_writer.events[0]

    self.assertEqual(event_object.data_type, u'windows:lnk:link')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.NOT_A_TIME)


if __name__ == '__main__':
  unittest.main()
