#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the for mactime parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import mactime

from tests.parsers import test_lib


class MactimeTest(test_lib.ParserTestCase):
  """Tests the for mactime parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = mactime.MactimeParser()
    storage_writer = self._ParseFile(['mactime.body'], parser)

    self.assertEqual(storage_writer.number_of_events, 67)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2012-05-25 15:59:43',
        'inode': 16,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[25], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2012-05-25 15:59:44',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[26], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2012-05-25 15:59:45',
        'filename': '/a_directory/another_file',
        'mode_as_string': 'r/rrw-------',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[27], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2012-05-25 16:17:43',
        'filename': '/passwordz\r.txt',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[38], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2020-07-30 06:41:05.354067456',
        'filename': '/file|with|pipes',
        'mode_as_string': 'r/rrwxrwxrwx',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[55], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2020-08-19 18:48:01',
        'filename': '/file_symboliclink1',
        'mode_as_string': 'l/lrwxrwxrwx',
        'symbolic_link_target': '/mnt/ext/testdir1/testfile1',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[64], expected_event_values)

  def testParseOnCorruptFile(self):
    """Tests the Parse function on a corrupt bodyfile."""
    parser = mactime.MactimeParser()
    storage_writer = self._ParseFile(['corrupt.body'], parser)

    self.assertEqual(storage_writer.number_of_events, 10)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 1)

    events = list(storage_writer.GetSortedEvents())

    # Event extracted from line with unescaped \r character.
    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2012-05-25 16:00:53',
        'filename': '/passwords\r.txt',
        'inode': 15,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Event extracted from line with unescaped \\ character.
    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'date_time': '2019-03-19 04:37:22',
        'filename': '/Windows\\System32',
        'inode': 75520,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)


if __name__ == '__main__':
  unittest.main()
