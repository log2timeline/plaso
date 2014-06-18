#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for PL-SQL recall file parser."""

import unittest

from plaso.formatters import pls_recall
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers import pls_recall
from plaso.parsers import test_lib


class PlsRecallTest(test_lib.ParserTestCase):
  """Tests for PL-SQL recall file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = pls_recall.PlsRecallParser(pre_obj)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['PLSRecall_Test.dat'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # There are two events in test file.
    self.assertEquals(len(event_objects), 2)

    event_object = event_objects[0]

    timestamp_expected = timelib_test.CopyStringToTimestamp(
        '2013-06-18 19:50:00:00:00')
    self.assertEqual(event_object.timestamp, timestamp_expected)

    sequence_expected = 206
    self.assertEqual(event_object.sequence, sequence_expected)

    username_expected = u'tsltmp'
    self.assertEqual(event_object.username, username_expected)

    database_name_expected = u'DB11'
    self.assertEqual(event_object.database_name, database_name_expected)

    # The test file actually has 'test_databae' in the SQL string.
    query_expected = u"SELECT * from test_databae where date > '01/01/2012'"
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
