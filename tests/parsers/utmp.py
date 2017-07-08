#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Parser test for utmp files."""

import unittest

from plaso.formatters import utmp  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import utmp

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class UtmpParserTest(test_lib.ParserTestCase):
  """The unit test for UTMP parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'utmp'])
  def testParseUtmpFile(self):
    """Tests the Parse function for an UTMP file."""
    parser_object = utmp.UtmpParser()
    storage_writer = self._ParseFile([u'utmp'], parser_object)

    self.assertEqual(storage_writer.number_of_events, 14)

    event_object = storage_writer.events[0]
    self.assertEqual(event_object.terminal, u'system boot')
    self.assertEqual(event_object.status, u'BOOT_TIME')

    event_object = storage_writer.events[1]
    self.assertEqual(event_object.status, u'RUN_LVL')

    event_object = storage_writer.events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-13 14:45:09')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'LOGIN')
    self.assertEqual(event_object.computer_name, u'localhost')
    self.assertEqual(event_object.terminal, u'tty4')
    self.assertEqual(event_object.status, u'LOGIN_PROCESS')
    self.assertEqual(event_object.exit, 0)
    self.assertEqual(event_object.pid, 1115)
    self.assertEqual(event_object.terminal_id, 52)
    expected_msg = (
        u'User: LOGIN '
        u'Computer Name: localhost '
        u'Terminal: tty4 '
        u'PID: 1115 '
        u'Terminal_ID: 52 '
        u'Status: LOGIN_PROCESS '
        u'IP Address: localhost '
        u'Exit: 0')
    expected_msg_short = (
        u'User: LOGIN')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = storage_writer.events[12]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-18 22:46:56.305504')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.computer_name, u'localhost')
    self.assertEqual(event_object.terminal, u'pts/4')
    self.assertEqual(event_object.status, u'USER_PROCESS')
    self.assertEqual(event_object.exit, 0)
    self.assertEqual(event_object.pid, 2684)
    self.assertEqual(event_object.terminal_id, 13359)
    expected_msg = (
        u'User: moxilo '
        u'Computer Name: localhost '
        u'Terminal: pts/4 '
        u'PID: 2684 '
        u'Terminal_ID: 13359 '
        u'Status: USER_PROCESS '
        u'IP Address: localhost '
        u'Exit: 0')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  @shared_test_lib.skipUnlessHasTestFile([u'wtmp.1'])
  def testParseWtmpFile(self):
    """Tests the Parse function for an WTMP file."""
    parser_object = utmp.UtmpParser()
    storage_writer = self._ParseFile([u'wtmp.1'], parser_object)

    self.assertEqual(storage_writer.number_of_events, 4)

    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-12-01 17:36:38.432935')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'userA')
    self.assertEqual(event_object.computer_name, u'10.10.122.1')
    self.assertEqual(event_object.terminal, u'pts/32')
    self.assertEqual(event_object.status, u'USER_PROCESS')
    self.assertEqual(event_object.ip_address, u'10.10.122.1')
    self.assertEqual(event_object.exit, 0)
    self.assertEqual(event_object.pid, 20060)
    self.assertEqual(event_object.terminal_id, 842084211)
    expected_msg = (
        u'User: userA '
        u'Computer Name: 10.10.122.1 '
        u'Terminal: pts/32 '
        u'PID: 20060 '
        u'Terminal_ID: 842084211 '
        u'Status: USER_PROCESS '
        u'IP Address: 10.10.122.1 '
        u'Exit: 0')
    expected_msg_short = (
        u'User: userA')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
