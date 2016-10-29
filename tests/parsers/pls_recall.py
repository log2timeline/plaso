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
    parser_object = pls_recall.PlsRecallParser()
    storage_writer = self._ParseFile([u'PLSRecall_Test.dat'], parser_object)

    # There are two events in test file.
    self.assertEqual(len(storage_writer.events), 2)

    event_object = storage_writer.events[0]

    timestamp_expected = timelib.Timestamp.CopyFromString(
        u'2013-06-18 19:50:00:00:00')
    self.assertEqual(event_object.timestamp, timestamp_expected)

    sequence_expected = 206
    self.assertEqual(event_object.sequence, sequence_expected)

    username_expected = u'tsltmp'
    self.assertEqual(event_object.username, username_expected)

    database_name_expected = u'DB11'
    self.assertEqual(event_object.database_name, database_name_expected)

    # The test file actually has 'test_databae' in the SQL string.
    query_expected = u'SELECT * from test_databae where date > \'01/01/2012\''
    self.assertEqual(event_object.query, query_expected)

    expected_msg = (
        u'Sequence #206 '
        u'User: tsltmp '
        u'Database Name: DB11 '
        u'Query: SELECT * from test_databae where date > \'01/01/2012\'')

    expected_msg_short = (
        u'206 tsltmp DB11 '
        u'SELECT * from test_databae where date > \'01/01/2012\'')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
