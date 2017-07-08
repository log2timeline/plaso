#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the selinux log file parser."""

import unittest

from plaso.formatters import selinux  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import selinux

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SELinuxUnitTest(test_lib.ParserTestCase):
  """Tests for the selinux log file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'selinux.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = selinux.SELinuxParser()
    knowledge_base_values = {u'year': 2013}
    storage_writer = self._ParseFile(
        [u'selinux.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 7)

    events = list(storage_writer.GetEvents())

    # Test case: normal entry.
    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-24 07:40:01.174')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        u'auid=4294967295 new auid=0 old ses=4294967295 new ses=1165')
    expected_short_message = (
        u'[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        u'auid=4294967295 new auid=...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test case: short date.
    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-24 07:40:01')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_string = u'[audit_type: SHORTDATE] check rounding'

    self._TestGetMessageStrings(event, expected_string, expected_string)

    # Test case: no msg.
    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-24 07:40:22.174')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_string = u'[audit_type: NOMSG]'

    self._TestGetMessageStrings(event, expected_string, expected_string)

    # Test case: under score.
    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-24 07:47:46.174')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        u'auid=4294967295 new auid=54321 old ses=4294967295 new ses=1166')
    expected_short_message = (
        u'[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        u'auid=4294967295 new...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
