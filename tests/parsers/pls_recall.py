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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # The test file actually has 'test_databae' in the table name.
    expected_event_values = {
        'data_type': 'PLSRecall:event',
        'database_name': 'DB11',
        'date_time': '2013-06-18 19:50:00.550000',
        'query': (
            'SELECT * from test_databae where date > \'01/01/2012\''),
        'sequence_number': 206,
        'username': 'tsltmp'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
