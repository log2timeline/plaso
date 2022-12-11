#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Restore Point (rp.log) file parser."""

import unittest

from plaso.parsers import winrestore

from tests.parsers import test_lib


class RestorePointLogParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Restore Point (rp.log) file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winrestore.RestorePointLogParser()
    storage_writer = self._ParseFile(['rp.log'], parser)

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
        'creation_time': '2015-03-23T18:38:14.2469544+00:00',
        'data_type': 'windows:restore_point:info',
        'description': 'Software Distribution Service 3.0',
        'restore_point_event_type': 102,
        'restore_point_type': 0}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
