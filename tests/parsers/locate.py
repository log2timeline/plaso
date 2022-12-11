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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Testing a path containing entries.
    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'entries': ['1', '2', '3', 'À'],
        'path': '/home/user/temp',
        'written_time': '2021-07-09T04:36:19.606373200+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Testing a path that is a subdirectory of the path tested above.
    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'entries': ['1a.txt', '1b.txt'],
        'path': '/home/user/temp/1',
        'written_time': '2021-07-09T04:11:07.438810500+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Testing a path without entries,
    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'entries': None,
        'path': '/home/user/temp/À',
        'written_time': '2021-07-09T04:36:19.606373200+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
