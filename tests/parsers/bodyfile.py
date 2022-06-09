#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the for bodyfile parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import bodyfile

from tests.parsers import test_lib


class BodyfileTest(test_lib.ParserTestCase):
  """Tests the for bodyfile parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = bodyfile.BodyfileParser()
    storage_writer = self._ParseFile(['bodyfile'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 71)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0

    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2012-05-25 15:59:43',
        'filename': '/a_directory/another_file',
        'group_identifier': 5000,
        'inode': 16,
        'owner_identifier': '151107',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[25], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2012-05-25 15:59:44',
        'filename': '/a_directory/another_file',
        'group_identifier': 5000,
        'inode': 16,
        'owner_identifier': '151107',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[26], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2012-05-25 15:59:45',
        'filename': '/a_directory/another_file',
        'group_identifier': 5000,
        'inode': 16,
        'mode_as_string': 'r/rrw-------',
        'owner_identifier': '151107',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[27], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2012-05-25 16:17:43',
        'filename': '/passwordz\r.txt',
        'group_identifier': 5000,
        'inode': 26,
        'owner_identifier': '151107',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[38], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2019-11-16 09:27:58.189698048',
        'filename': '\\testdir2',
        'group_identifier': None,
        'inode': 48,
        'owner_identifier': None,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[50], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2020-07-30 06:41:05.354067456',
        'filename': '/file|with|pipes',
        'group_identifier': 0,
        'inode': 64,
        'mode_as_string': 'r/rrwxrwxrwx',
        'owner_identifier': '48',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE}

    self.CheckEventValues(storage_writer, events[59], expected_event_values)

    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2020-08-19 18:48:01',
        'filename': '/file_symboliclink1',
        'group_identifier': 1000,
        'inode': 16,
        'mode_as_string': 'l/lrwxrwxrwx',
        'owner_identifier': '1000',
        'symbolic_link_target': '/mnt/ext/testdir1/testfile1',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[68], expected_event_values)

  def testParseOnCorruptFile(self):
    """Tests the Parse function on a corrupt bodyfile."""
    parser = bodyfile.BodyfileParser()
    storage_writer = self._ParseFile(['bodyfile.corrupt'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 1)

    events = list(storage_writer.GetSortedEvents())

    # Event extracted from line with unescaped \r character.
    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2012-05-25 16:00:53',
        'filename': '/passwords\r.txt',
        'inode': 15,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Event extracted from line with unescaped \\ character.
    expected_event_values = {
        'data_type': 'fs:bodyfile:entry',
        'date_time': '2019-03-19 04:37:22',
        'filename': '/Windows\\System32',
        'inode': 75520,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)


if __name__ == '__main__':
  unittest.main()
