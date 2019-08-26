#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for PL-SQL recall file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import pls_recall as _  # pylint: disable=unused-import
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

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-06-18 19:50:00.550000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.sequence_number, 206)
    self.assertEqual(event_data.username, 'tsltmp')
    self.assertEqual(event_data.database_name, 'DB11')

    # The test file actually has 'test_databae' in the SQL string.
    expected_query = 'SELECT * from test_databae where date > \'01/01/2012\''
    self.assertEqual(event_data.query, expected_query)

    expected_message = (
        'Sequence number: 206 '
        'Username: tsltmp '
        'Database name: DB11 '
        'Query: {0:s}').format(expected_query)

    expected_short_message = '206 tsltmp DB11 {0:s}'.format(expected_query)

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
