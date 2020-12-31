#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parser test for utmp files."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import utmp

from tests.parsers import test_lib


class UtmpParserTest(test_lib.ParserTestCase):
  """The unit test for utmp parser."""

  def testParseUtmpFile(self):
    """Tests the Parse function on a utmp file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['utmp'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'terminal': 'system boot',
        'type': 2}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'type': 1}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'exit_status': 0,
        'hostname': 'localhost',
        'pid': 1115,
        'terminal_identifier': 52,
        'terminal': 'tty4',
        'timestamp': '2013-12-13 14:45:09.000000',
        'type': 6,
        'username': 'LOGIN'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_message = (
        'User: LOGIN '
        'Hostname: localhost '
        'Terminal: tty4 '
        'PID: 1115 '
        'Terminal identifier: 52 '
        'Status: LOGIN_PROCESS '
        'IP Address: 0.0.0.0 '
        'Exit status: 0')
    expected_short_message = (
        'User: LOGIN '
        'PID: 1115 '
        'Status: LOGIN_PROCESS')

    event_data = self._GetEventDataOfEvent(storage_writer, events[2])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'exit_status': 0,
        'hostname': 'localhost',
        'pid': 2684,
        'terminal_identifier': 13359,
        'terminal': 'pts/4',
        'timestamp': '2013-12-18 22:46:56.305504',
        'type': 7,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[12], expected_event_values)

    expected_message = (
        'User: moxilo '
        'Hostname: localhost '
        'Terminal: pts/4 '
        'PID: 2684 '
        'Terminal identifier: 13359 '
        'Status: USER_PROCESS '
        'IP Address: 0.0.0.0 '
        'Exit status: 0')
    expected_short_message = (
        'User: moxilo '
        'PID: 2684 '
        'Status: USER_PROCESS')

    event_data = self._GetEventDataOfEvent(storage_writer, events[12])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseWtmpFile(self):
    """Tests the Parse function on a wtmp file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['wtmp.1'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'exit_status': 0,
        'hostname': '10.10.122.1',
        'ip_address': '10.10.122.1',
        'pid': 20060,
        'terminal_identifier': 842084211,
        'terminal': 'pts/32',
        'timestamp': '2011-12-01 17:36:38.432935',
        'type': 7,
        'username': 'userA'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'User: userA '
        'Hostname: 10.10.122.1 '
        'Terminal: pts/32 '
        'PID: 20060 '
        'Terminal identifier: 842084211 '
        'Status: USER_PROCESS '
        'IP Address: 10.10.122.1 '
        'Exit status: 0')
    expected_short_message = (
        'User: userA '
        'PID: 20060 '
        'Status: USER_PROCESS')

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
