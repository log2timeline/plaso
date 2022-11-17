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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'path': '/home/user/temp',
        'contents': ['1', '2', '3', 'À'],
        'written_time': '2021-07-09T04:36:19.606373200+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'path': '/home/user/temp/1',
        'contents': ['1a.txt', '1b.txt'],
        'written_time': '2021-07-09T04:11:07.438810500+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'path': '/home/user/temp/2',
        'contents': [],
        'written_time': '2021-07-09T04:10:54.884843500+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'path': '/home/user/temp/3',
        'contents': ['3a.txt', '3b.txt', '3c'],
        'written_time': '2021-07-09T04:11:25.146217000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'path': '/home/user/temp/3/3c',
        'contents': [],
        'written_time': '2021-07-09T04:11:25.146217000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'linux:locate_database:entry',
        'path': '/home/user/temp/À',
        'contents': [],
        'written_time': '2021-07-09T04:36:19.606373200+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
