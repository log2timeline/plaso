#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows recycler parsers."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import recycler as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import recycler

from tests.parsers import test_lib


class WinRecycleBinParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycle Bin parser."""

  def testParseVista(self):
    """Tests the Parse function on a Windows Vista RecycleBin file."""
    parser = recycler.WinRecycleBinParser()
    storage_writer = self._ParseFile(['$II3DF3L.zip'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-03-12 20:49:58.633000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_filename = (
        'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip')
    self.assertEqual(event_data.original_filename, expected_filename)
    self.assertEqual(event_data.file_size, 724919)

    expected_message = '{0:s} (from drive: UNKNOWN)'.format(expected_filename)
    expected_short_message = 'Deleted file: {0:s}'.format(expected_filename)
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseWindows10(self):
    """Tests the Parse function on a Windows 10 RecycleBin file."""
    parser = recycler.WinRecycleBinParser()
    storage_writer = self._ParseFile(['$I103S5F.jpg'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2016-06-29 21:37:45.618000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_filename = (
        'C:\\Users\\random\\Downloads\\bunnies.jpg')
    self.assertEqual(event_data.original_filename, expected_filename)
    self.assertEqual(event_data.file_size, 222255)

    expected_message = '{0:s} (from drive: UNKNOWN)'.format(expected_filename)
    expected_short_message = 'Deleted file: {0:s}'.format(expected_filename)
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


class WinRecyclerInfo2ParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycler INFO2 parser."""

  def testParse(self):
    """Reads an INFO2 file and run a few tests."""
    parser = recycler.WinRecyclerInfo2Parser()
    storage_writer = self._ParseFile(['INFO2'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2004-08-25 16:18:25.237000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_DELETED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_filename = (
        'C:\\Documents and Settings\\Mr. Evil\\Desktop\\lalsetup250.exe')
    self.assertEqual(event_data.original_filename, expected_filename)
    self.assertEqual(event_data.record_index, 1)

    event = events[1]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'DC2 -> C:\\Documents and Settings\\Mr. Evil\\Desktop'
        '\\netstumblerinstaller_0_4_0.exe (from drive: C)')
    expected_short_message = (
        'Deleted file: C:\\Documents and Settings\\Mr. Evil\\Desktop'
        '\\netstumblerinstaller...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[2]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self._TestGetSourceStrings(event, event_data, 'Recycle Bin', 'RECBIN')


if __name__ == '__main__':
  unittest.main()
