#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows recycler parsers."""

import unittest

from plaso.parsers import recycler

from tests.parsers import test_lib


class WinRecycleBinParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycle Bin parser."""

  def testParseVista(self):
    """Tests the Parse function on a Windows Vista RecycleBin file."""
    parser = recycler.WinRecycleBinParser()
    storage_writer = self._ParseFile(['$II3DF3L.zip'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:metadata:deleted_item',
        'deletion_time': '2012-03-12T20:49:58.6330000+00:00',
        'file_size': 724919,
        'original_filename': (
            'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWindows10(self):
    """Tests the Parse function on a Windows 10 RecycleBin file."""
    parser = recycler.WinRecycleBinParser()
    storage_writer = self._ParseFile(['$I103S5F.jpg'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:metadata:deleted_item',
        'deletion_time': '2016-06-29T21:37:45.6180000+00:00',
        'file_size': 222255,
        'original_filename': (
            'C:\\Users\\random\\Downloads\\bunnies.jpg')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class WinRecyclerInfo2ParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycler INFO2 parser."""

  def testParse(self):
    """Tests the Parse function on a Windows Recycler INFO2 file."""
    parser = recycler.WinRecyclerInfo2Parser()
    storage_writer = self._ParseFile(['INFO2'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:metadata:deleted_item',
        'deletion_time': '2004-08-25T16:18:25.2370000+00:00',
        'drive_number': 2,
        'original_filename': (
            'C:\\Documents and Settings\\Mr. Evil\\Desktop\\lalsetup250.exe'),
        'record_index': 1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
