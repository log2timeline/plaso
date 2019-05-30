#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the selinux log file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import selinux as _  # pylint: disable=unused-import
from plaso.parsers import selinux

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SELinuxUnitTest(test_lib.ParserTestCase):
  """Tests for the selinux log file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['selinux.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = selinux.SELinuxParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['selinux.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 4)
    self.assertEqual(storage_writer.number_of_events, 7)

    events = list(storage_writer.GetEvents())

    # Test case: normal entry.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-05-24 07:40:01.174000')

    expected_message = (
        '[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        'auid=4294967295 new auid=0 old ses=4294967295 new ses=1165')
    expected_short_message = (
        '[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        'auid=4294967295 new auid=...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test case: short date.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2012-05-24 07:40:01.000000')

    expected_string = '[audit_type: SHORTDATE] check rounding'

    self._TestGetMessageStrings(event, expected_string, expected_string)

    # Test case: no msg.
    event = events[2]

    self.CheckTimestamp(event.timestamp, '2012-05-24 07:40:22.174000')

    expected_string = '[audit_type: NOMSG]'

    self._TestGetMessageStrings(event, expected_string, expected_string)

    # Test case: under score.
    event = events[3]

    self.CheckTimestamp(event.timestamp, '2012-05-24 07:47:46.174000')

    expected_message = (
        '[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        'auid=4294967295 new auid=54321 old ses=4294967295 new ses=1166')
    expected_short_message = (
        '[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        'auid=4294967295 new...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
