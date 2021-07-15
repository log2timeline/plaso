#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for locate database file parser."""

import unittest

from plaso.parsers import locate

from tests.parsers import test_lib


class LocateUnitTest(test_lib.ParserTestCase):
  """Tests for Locate Database file parser."""

  def testParseFile(self):
    """Test parsing of a Locate Database file."""
    parser = locate.LocateDatabaseParser()
    storage_writer = self._ParseFile(['mlocate.db'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {'folder_path': '/home/user/temp',
      'date_time': '2021-07-09 04:36:19.606373200'}
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {'folder_path': '/home/user/temp/1',
      'date_time': '2021-07-09 04:11:07.438810500'}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {'folder_path': '/home/user/temp/2',
      'date_time': '2021-07-09 04:10:54.884843500'}
    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {'folder_path': '/home/user/temp/3',
      'date_time': '2021-07-09 04:11:25.146217000'}
    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {'folder_path': '/home/user/temp/3/3c',
      'date_time': '2021-07-09 04:11:25.146217000'}
    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {'folder_path': '/home/user/temp/À',
      'date_time': '2021-07-09 04:36:19.606373200'}
    self.CheckEventValues(storage_writer, events[5], expected_event_values)


if __name__ == '__main__':
  unittest.main()
