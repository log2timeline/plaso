#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parser test for utmp files."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import utmp as _  # pylint: disable=unused-import
from plaso.parsers import utmp

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class UtmpParserTest(test_lib.ParserTestCase):
  """The unit test for utmp parser."""

  @shared_test_lib.skipUnlessHasTestFile(['utmp'])
  def testParseUtmpFile(self):
    """Tests the Parse function on a utmp file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['utmp'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetEvents())

    event = events[0]
    self.assertEqual(event.terminal, 'system boot')
    self.assertEqual(event.type, 2)

    event = events[1]
    self.assertEqual(event.type, 1)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-12-13 14:45:09.000000')

    self.assertEqual(event.username, 'LOGIN')
    self.assertEqual(event.hostname, 'localhost')
    self.assertEqual(event.terminal, 'tty4')
    self.assertEqual(event.type, 6)
    self.assertEqual(event.exit_status, 0)
    self.assertEqual(event.pid, 1115)
    self.assertEqual(event.terminal_identifier, 52)

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
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[12]

    self.CheckTimestamp(event.timestamp, '2013-12-18 22:46:56.305504')

    self.assertEqual(event.username, 'moxilo')
    self.assertEqual(event.hostname, 'localhost')
    self.assertEqual(event.terminal, 'pts/4')
    self.assertEqual(event.type, 7)
    self.assertEqual(event.exit_status, 0)
    self.assertEqual(event.pid, 2684)
    self.assertEqual(event.terminal_identifier, 13359)

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
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['wtmp.1'])
  def testParseWtmpFile(self):
    """Tests the Parse function on a wtmp file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['wtmp.1'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2011-12-01 17:36:38.432935')

    self.assertEqual(event.username, 'userA')
    self.assertEqual(event.hostname, '10.10.122.1')
    self.assertEqual(event.terminal, 'pts/32')
    self.assertEqual(event.type, 7)
    self.assertEqual(event.ip_address, '10.10.122.1')
    self.assertEqual(event.exit_status, 0)
    self.assertEqual(event.pid, 20060)
    self.assertEqual(event.terminal_identifier, 842084211)

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
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
