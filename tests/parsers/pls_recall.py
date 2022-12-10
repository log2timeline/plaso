#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for PL-SQL recall file parser."""

import unittest

from plaso.parsers import pls_recall

from tests.parsers import test_lib


class PlsRecallTest(test_lib.ParserTestCase):
  """Tests for PL-SQL recall file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = pls_recall.PlsRecallParser()
    storage_writer = self._ParseFile(['PLSRecall_Test.dat'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Note that the test file actually has 'test_databae' in the table name.
    expected_event_values = {
        'data_type': 'pls_recall:entry',
        'database_name': 'DB11',
        'query': 'SELECT * from test_databae where date > \'01/01/2012\'',
        'sequence_number': 206,
        'username': 'tsltmp',
        'written_time': '2013-06-18T19:50:00.550000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
