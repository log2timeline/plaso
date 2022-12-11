#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Fish History file parser."""

import unittest

from plaso.parsers import fish_history

from tests.parsers import test_lib


class FishHistoryTest(test_lib.ParserTestCase):
  """Tests for Fish History file parser."""

  def testParseFile(self):
    """Test parsing of a Fish History file."""
    parser = fish_history.FishHistoryParser()
    storage_writer = self._ParseFile(['fish_history'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': 'll',
        'data_type': 'fish:history:entry',
        'written_time': '2021-04-29T22:53:00+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
