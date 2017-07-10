#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for PL-SQL recall file parser."""

import unittest

from plaso.formatters import pls_recall  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import pls_recall

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class PlsRecallTest(test_lib.ParserTestCase):
  """Tests for PL-SQL recall file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'PLSRecall_Test.dat'])
  def testParse(self):
    """Tests the Parse function."""
    parser = pls_recall.PlsRecallParser()
    storage_writer = self._ParseFile([u'PLSRecall_Test.dat'], parser)

    # There are two events in test file.
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    timestamp_expected = timelib.Timestamp.CopyFromString(
        u'2013-06-18 19:50:00.550')
    self.assertEqual(event.timestamp, timestamp_expected)

    self.assertEqual(event.sequence_number, 206)
    self.assertEqual(event.username, u'tsltmp')
    self.assertEqual(event.database_name, u'DB11')

    # The test file actually has 'test_databae' in the SQL string.
    expected_query = u'SELECT * from test_databae where date > \'01/01/2012\''
    self.assertEqual(event.query, expected_query)

    expected_message = (
        u'Sequence number: 206 '
        u'Username: tsltmp '
        u'Database name: DB11 '
        u'Query: {0:s}').format(expected_query)

    expected_short_message = u'206 tsltmp DB11 {0:s}'.format(expected_query)

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
