#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for PL-SQL recall file parser."""

import unittest

from plaso.formatters import pls_recall as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import pls_recall

from tests.parsers import test_lib


class PlsRecallTest(test_lib.ParserTestCase):
  """Tests for PL-SQL recall file parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = pls_recall.PlsRecallParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'PLSRecall_Test.dat'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # There are two events in test file.
    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

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
