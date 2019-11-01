#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for santa log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import santa as _  # pylint: disable=unused-import
from plaso.parsers import santa

from tests.parsers import test_lib


class SantaUnitTest(test_lib.ParserTestCase):
  """Tests for santa log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = santa.SantaParser()
    storage_writer = self._ParseFile(['santa.log'], parser)

    # Test file contains 194 lines
    # - 3 lines should be skipped in the results.
    # - 17 new events should be added from existing lines.

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 208)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # Execution event with quarantine url.
    event = events[46]
    self.CheckTimestamp(event.timestamp, '2018-08-19 03:17:55.765000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event_data.quarantine_url,
        'https://endpoint920510.azureedge.net/s4l/s4l/download/mac/'
        'Skype-8.28.0.41.dmg')

    expected_message = (
        'Santa ALLOW process: /Applications/Skype.app/Contents/MacOS/Skype hash'
        ': 78b43a13b5b608fe1a5a590f5f3ff112ff16ece7befc29fc84347125f6b9ca78')
    expected_short_message = (
        'ALLOW process: /Applications/Skype.app/Contents/MacOS/Skype')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # File operation event log
    event = events[159]
    self.CheckTimestamp(event.timestamp, '2018-08-19 04:02:47.911000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    # Test common fields in file operation event.
    self.assertEqual(event_data.action, 'WRITE')
    self.assertEqual(event_data.file_path, '/Users/qwerty/newfile')
    self.assertEqual(event_data.pid, '303')
    self.assertEqual(event_data.ppid, '1')
    self.assertEqual(event_data.process, 'Finder')
    self.assertEqual(
        event_data.process_path,
        '/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder')
    self.assertEqual(event_data.uid, '501')
    self.assertEqual(event_data.user, 'qwerty')
    self.assertEqual(event_data.gid, '20')
    self.assertEqual(event_data.group, 'staff')

    expected_message = (
        'Santa WRITE event /Users/qwerty/newfile by process: '
        '/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder')
    expected_short_message = 'File WRITE on: /Users/qwerty/newfile'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Disk mounts event log.
    event = events[38]
    self.CheckTimestamp(event.timestamp, '2018-08-19 03:17:29.036000')

    # Test common fields in file Disk mounts event.
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.action, 'DISKAPPEAR')
    self.assertEqual(event_data.mount, '')
    self.assertEqual(event_data.volume, 'Skype')
    self.assertEqual(event_data.bsd_name, 'disk2s1')
    self.assertEqual(event_data.fs, 'hfs')
    self.assertEqual(event_data.model, 'Apple Disk Image')
    self.assertEqual(event_data.serial, '')
    self.assertEqual(event_data.bus, 'Virtual Interface')
    self.assertEqual(
        event_data.dmg_path, '/Users/qwerty/Downloads/Skype-8.28.0.41.dmg')
    self.assertEqual(event_data.appearance, '2018-08-19T03:17:28.982Z')

    expected_message = (
        'Santa DISKAPPEAR for (/Users/qwerty/Downloads/Skype-8.28.0.41.dmg)')
    expected_short_message = 'DISKAPPEAR Skype'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test Disk event created from appearance timestamp.
    event = events[35]
    self.CheckTimestamp(event.timestamp, '2018-08-19 03:17:28.982000')
    self.assertEqual(event.timestamp_desc, 'First Connection Time')


if __name__ == '__main__':
  unittest.main()
