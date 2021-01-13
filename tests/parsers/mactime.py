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

    # The file contains 17 lines x 4 timestamps per line, which should be
    # 68 events in total. However several of these events have an empty
    # timestamp value and are omitted.
    # Total entries: ( 11 * 3 ) + ( 6 * 4 ) = 41

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 60)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'inode': 16,
        'timestamp': '2012-05-25 15:59:43.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[21], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'timestamp': '2012-05-25 15:59:44.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[22], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'filename': '/a_directory/another_file',
        'mode_as_string': 'r/rrw-------',
        'timestamp': '2012-05-25 15:59:45.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[23], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'filename': '/file|with|pipes',
        'mode_as_string': 'r/rrwxrwxrwx',
        'timestamp': '2020-07-30 06:41:05.354067',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[48], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:mactime:line',
        'filename': '/file_symboliclink1',
        'mode_as_string': 'l/lrwxrwxrwx',
        'symbolic_link_target': '/mnt/ext/testdir1/testfile1',
        'timestamp': '2020-08-19 18:48:01.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[57], expected_event_values)


if __name__ == '__main__':
  unittest.main()
