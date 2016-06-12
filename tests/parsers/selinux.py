#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the selinux log file parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import selinux as selinux_formatter
from plaso.parsers import selinux

from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SELinuxUnitTest(test_lib.ParserTestCase):
  """Tests for the selinux log file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = selinux.SELinuxParser()
    knowledge_base_values = {u'year': 2013}
    storage_writer = self._ParseFile(
        [u'selinux.log'], parser_object,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 5)

    # Test case: normal entry.
    event_object = storage_writer.events[0]

    self.assertEqual(event_object.timestamp, 1337845201174000)

    expected_msg = (
        u'[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        u'auid=4294967295 new auid=0 old ses=4294967295 new ses=1165')
    expected_msg_short = (
        u'[audit_type: LOGIN, pid: 25443] pid=25443 uid=0 old '
        u'auid=4294967295 new auid=...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # Test case: short date.
    event_object = storage_writer.events[1]

    self.assertEqual(event_object.timestamp, 1337845201000000)

    expected_string = u'[audit_type: SHORTDATE] check rounding'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Test case: no msg.
    event_object = storage_writer.events[2]

    self.assertEqual(event_object.timestamp, 1337845222174000)

    expected_string = u'[audit_type: NOMSG]'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Test case: under score.
    event_object = storage_writer.events[3]

    self.assertEqual(event_object.timestamp, 1337845666174000)

    expected_msg = (
        u'[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        u'auid=4294967295 new auid=54321 old ses=4294967295 new ses=1166')
    expected_msg_short = (
        u'[audit_type: UNDER_SCORE, pid: 25444] pid=25444 uid=0 old '
        u'auid=4294967295 new...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
