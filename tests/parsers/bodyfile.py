#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the for bodyfile parser."""

import unittest

from plaso.parsers import bodyfile

from tests.parsers import test_lib


class BodyfileTest(test_lib.ParserTestCase):
  """Tests the for bodyfile parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = bodyfile.BodyfileParser()
    storage_writer = self._ParseFile(['bodyfile'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 24)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0

    expected_event_values = {
        'access_time': '2012-05-25T15:59:43',
        'change_time': '2012-05-25T15:59:45',
        'creation_time': None,
        'data_type': 'fs:bodyfile:entry',
        'filename': '/a_directory/another_file',
        'group_identifier': 5000,
        'inode': 16,
        'modification_time': '2012-05-25T15:59:44',
        'owner_identifier': '151107'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testParseOnCorruptFile(self):
    """Tests the Parse function on a corrupt bodyfile."""
    parser = bodyfile.BodyfileParser()
    storage_writer = self._ParseFile(['bodyfile.corrupt'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 1)

    # Event data extracted from line with unescaped \r character.
    expected_event_values = {
        'access_time': '2012-05-25T16:00:53',
        'change_time': '2012-05-25T16:01:03',
        'creation_time': None,
        'data_type': 'fs:bodyfile:entry',
        'filename': '/passwords\r.txt',
        'inode': 15,
        'modification_time': '2012-05-25T16:00:53'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Event data extracted from line with unescaped \\ character.
    expected_event_values = {
        'access_time': '2021-01-12T12:26:01',
        'change_time': '2019-03-19T04:37:22',
        'creation_time': '2019-03-19T04:37:22',
        'data_type': 'fs:bodyfile:entry',
        'filename': '/Windows\\System32',
        'inode': 75520,
        'modification_time': '2021-01-12T12:26:01'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
