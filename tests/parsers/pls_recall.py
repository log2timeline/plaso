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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    # The test file actually has 'test_databae' in the table name.
    expected_event_values = {
        'data_type': 'PLSRecall:event',
        'database_name': 'DB11',
        'query': (
            'SELECT * from test_databae where date > \'01/01/2012\''),
        'sequence_number': 206,
        'timestamp': '2013-06-18 19:50:00.550000',
        'username': 'tsltmp'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
