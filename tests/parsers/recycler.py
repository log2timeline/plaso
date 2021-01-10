#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows recycler parsers."""

import unittest

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

    expected_event_values = {
        'data_type': 'windows:metadata:deleted_item',
        'file_size': 724919,
        'original_filename': (
            'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip'),
        'timestamp': '2012-03-12 20:49:58.633000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseWindows10(self):
    """Tests the Parse function on a Windows 10 RecycleBin file."""
    parser = recycler.WinRecycleBinParser()
    storage_writer = self._ParseFile(['$I103S5F.jpg'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'windows:metadata:deleted_item',
        'file_size': 222255,
        'original_filename': (
            'C:\\Users\\random\\Downloads\\bunnies.jpg'),
        'timestamp': '2016-06-29 21:37:45.618000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


class WinRecyclerInfo2ParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycler INFO2 parser."""

  def testParse(self):
    """Tests the Parse function on a Windows Recycler INFO2 file."""
    parser = recycler.WinRecyclerInfo2Parser()
    storage_writer = self._ParseFile(['INFO2'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'windows:metadata:deleted_item',
        'drive_number': 2,
        'original_filename': (
            'C:\\Documents and Settings\\Mr. Evil\\Desktop\\lalsetup250.exe'),
        'record_index': 1,
        'timestamp': '2004-08-25 16:18:25.237000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_DELETED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
