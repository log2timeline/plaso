#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for UTMPX file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import utmpx as _  # pylint: disable=unused-import
from plaso.parsers import utmpx

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class UtmpxParserTest(test_lib.ParserTestCase):
  """Tests for utmpx file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['utmpx_mac'])
  def testParse(self):
    """Tests the Parse function."""
    parser = utmpx.UtmpxParser()
    storage_writer = self._ParseFile(['utmpx_mac'], parser)

    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-11-13 17:52:34.000000')

    expected_message = (
        'User: N/A Status: BOOT_TIME '
        'Computer Name: localhost Terminal: N/A')
    expected_short_message = 'User: N/A'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-11-13 17:52:41.736713')

    self.assertEqual(event.user, 'moxilo')
    self.assertEqual(event.terminal, 'console', )
    self.assertEqual(event.status_type, 7)
    self.assertEqual(event.computer_name, 'localhost')

    expected_message = (
        'User: moxilo Status: '
        'USER_PROCESS '
        'Computer Name: localhost '
        'Terminal: console')
    expected_short_message = 'User: moxilo'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2013-11-14 04:32:56.641464')

    self.assertEqual(event.user, 'moxilo')
    self.assertEqual(event.terminal, 'ttys002')
    self.assertEqual(event.status_type, 8)

    expected_message = (
        'User: moxilo Status: '
        'DEAD_PROCESS '
        'Computer Name: localhost '
        'Terminal: ttys002')
    expected_short_message = 'User: moxilo'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
