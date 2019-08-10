#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for UTMPX file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import utmpx as _  # pylint: disable=unused-import
from plaso.parsers import utmpx

from tests.parsers import test_lib


class UtmpxParserTest(test_lib.ParserTestCase):
  """Tests for utmpx file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = utmpx.UtmpxParser()
    storage_writer = self._ParseFile(['utmpx_mac'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-11-13 17:52:34.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Status: BOOT_TIME '
        'Hostname: localhost '
        'PID: 1 '
        'Terminal identifier: 0')
    expected_short_message = (
        'PID: 1 '
        'Status: BOOT_TIME')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-11-13 17:52:41.736713')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.username, 'moxilo')
    self.assertEqual(event_data.terminal, 'console')
    self.assertEqual(event_data.type, 7)
    self.assertEqual(event_data.hostname, 'localhost')

    expected_message = (
        'User: moxilo '
        'Status: USER_PROCESS '
        'Hostname: localhost '
        'Terminal: console '
        'PID: 67 '
        'Terminal identifier: 65583')
    expected_short_message = (
        'User: moxilo '
        'PID: 67 '
        'Status: USER_PROCESS')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2013-11-14 04:32:56.641464')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.username, 'moxilo')
    self.assertEqual(event_data.terminal, 'ttys002')
    self.assertEqual(event_data.type, 8)

    expected_message = (
        'User: moxilo '
        'Status: DEAD_PROCESS '
        'Hostname: localhost '
        'Terminal: ttys002 '
        'PID: 6899 '
        'Terminal identifier: 842018931')
    expected_short_message = (
        'User: moxilo '
        'PID: 6899 '
        'Status: DEAD_PROCESS')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
