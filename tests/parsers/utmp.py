#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Parser test for utmp files."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import utmp as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import utmp

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class UtmpParserTest(test_lib.ParserTestCase):
  """The unit test for UTMP parser."""

  @shared_test_lib.skipUnlessHasTestFile(['utmp'])
  def testParseUtmpFile(self):
    """Tests the Parse function for an UTMP file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['utmp'], parser)

    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetEvents())

    event = events[0]
    self.assertEqual(event.terminal, 'system boot')
    self.assertEqual(event.status, 'BOOT_TIME')

    event = events[1]
    self.assertEqual(event.status, 'RUN_LVL')

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-13 14:45:09')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.user, 'LOGIN')
    self.assertEqual(event.computer_name, 'localhost')
    self.assertEqual(event.terminal, 'tty4')
    self.assertEqual(event.status, 'LOGIN_PROCESS')
    self.assertEqual(event.exit, 0)
    self.assertEqual(event.pid, 1115)
    self.assertEqual(event.terminal_id, 52)
    expected_message = (
        'User: LOGIN '
        'Computer Name: localhost '
        'Terminal: tty4 '
        'PID: 1115 '
        'Terminal_ID: 52 '
        'Status: LOGIN_PROCESS '
        'IP Address: localhost '
        'Exit: 0')
    expected_short_message = (
        'User: LOGIN')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[12]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-18 22:46:56.305504')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.user, 'moxilo')
    self.assertEqual(event.computer_name, 'localhost')
    self.assertEqual(event.terminal, 'pts/4')
    self.assertEqual(event.status, 'USER_PROCESS')
    self.assertEqual(event.exit, 0)
    self.assertEqual(event.pid, 2684)
    self.assertEqual(event.terminal_id, 13359)
    expected_message = (
        'User: moxilo '
        'Computer Name: localhost '
        'Terminal: pts/4 '
        'PID: 2684 '
        'Terminal_ID: 13359 '
        'Status: USER_PROCESS '
        'IP Address: localhost '
        'Exit: 0')
    expected_short_message = (
        'User: moxilo')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['wtmp.1'])
  def testParseWtmpFile(self):
    """Tests the Parse function for an WTMP file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['wtmp.1'], parser)

    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2011-12-01 17:36:38.432935')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.user, 'userA')
    self.assertEqual(event.computer_name, '10.10.122.1')
    self.assertEqual(event.terminal, 'pts/32')
    self.assertEqual(event.status, 'USER_PROCESS')
    self.assertEqual(event.ip_address, '10.10.122.1')
    self.assertEqual(event.exit, 0)
    self.assertEqual(event.pid, 20060)
    self.assertEqual(event.terminal_id, 842084211)
    expected_message = (
        'User: userA '
        'Computer Name: 10.10.122.1 '
        'Terminal: pts/32 '
        'PID: 20060 '
        'Terminal_ID: 842084211 '
        'Status: USER_PROCESS '
        'IP Address: 10.10.122.1 '
        'Exit: 0')
    expected_short_message = (
        'User: userA')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
