#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for UTMPX file parser."""

import unittest

from plaso.formatters import utmpx  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import utmpx

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class UtmpxParserTest(test_lib.ParserTestCase):
  """Tests for utmpx file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'utmpx_mac'])
  def testParse(self):
    """Tests the Parse function."""
    parser = utmpx.UtmpxParser()
    storage_writer = self._ParseFile([u'utmpx_mac'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-13 17:52:34')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'User: N/A Status: BOOT_TIME '
        u'Computer Name: localhost Terminal: N/A')
    expected_short_message = u'User: N/A'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-13 17:52:41.736713')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.user, u'moxilo')
    self.assertEqual(event.terminal, u'console', )
    self.assertEqual(event.status_type, 7)
    self.assertEqual(event.computer_name, u'localhost')

    expected_message = (
        u'User: moxilo Status: '
        u'USER_PROCESS '
        u'Computer Name: localhost '
        u'Terminal: console')
    expected_short_message = u'User: moxilo'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-14 04:32:56.641464')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.user, u'moxilo')
    self.assertEqual(event.terminal, u'ttys002')
    self.assertEqual(event.status_type, 8)

    expected_message = (
        u'User: moxilo Status: '
        u'DEAD_PROCESS '
        u'Computer Name: localhost '
        u'Terminal: ttys002')
    expected_short_message = u'User: moxilo'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
