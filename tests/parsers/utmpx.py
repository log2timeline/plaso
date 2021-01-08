#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for UTMPX file parser."""

import unittest

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

    expected_event_values = {
        'timestamp': '2013-11-13 17:52:34.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Status: BOOT_TIME '
        'Hostname: localhost '
        'PID: 1 '
        'Terminal identifier: 0')
    expected_short_message = (
        'PID: 1 '
        'Status: BOOT_TIME')

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'hostname': 'localhost',
        'terminal': 'console',
        'timestamp': '2013-11-13 17:52:41.736713',
        'type': 7,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

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

    event_data = self._GetEventDataOfEvent(storage_writer, events[1])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'terminal': 'ttys002',
        'timestamp': '2013-11-14 04:32:56.641464',
        'type': 8,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

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

    event_data = self._GetEventDataOfEvent(storage_writer, events[4])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
