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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2012-03-12 20:49:58.6330000',
        'data_type': 'windows:metadata:deleted_item',
        'file_size': 724919,
        'original_filename': (
            'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseWindows10(self):
    """Tests the Parse function on a Windows 10 RecycleBin file."""
    parser = recycler.WinRecycleBinParser()
    storage_writer = self._ParseFile(['$I103S5F.jpg'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2016-06-29 21:37:45.6180000',
        'data_type': 'windows:metadata:deleted_item',
        'file_size': 222255,
        'original_filename': (
            'C:\\Users\\random\\Downloads\\bunnies.jpg')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


class WinRecyclerInfo2ParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycler INFO2 parser."""

  def testParse(self):
    """Tests the Parse function on a Windows Recycler INFO2 file."""
    parser = recycler.WinRecyclerInfo2Parser()
    storage_writer = self._ParseFile(['INFO2'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2004-08-25 16:18:25.2370000',
        'data_type': 'windows:metadata:deleted_item',
        'drive_number': 2,
        'original_filename': (
            'C:\\Documents and Settings\\Mr. Evil\\Desktop\\lalsetup250.exe'),
        'record_index': 1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_DELETED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
