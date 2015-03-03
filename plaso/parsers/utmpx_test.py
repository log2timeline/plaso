#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for UTMPX file parser."""

import unittest

from plaso.formatters import utmpx as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import test_lib
from plaso.parsers import utmpx


class UtmpxParserTest(test_lib.ParserTestCase):
  """Tests for utmpx file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = utmpx.UtmpxParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['utmpx_mac'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 6)

    event_object = event_objects[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-13 17:52:34')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg_short = u'User: N/A'
    expected_msg = (
        u'User: N/A Status: BOOT_TIME '
        u'Computer Name: localhost Terminal: N/A')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-13 17:52:41.736713')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.terminal, u'console', )
    self.assertEqual(event_object.status, u'USER_PROCESS')
    self.assertEqual(event_object.computer_name, u'localhost')
    expected_msg = (
        u'User: moxilo Status: '
        u'USER_PROCESS '
        u'Computer Name: localhost '
        u'Terminal: console')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-11-14 04:32:56.641464')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.user, u'moxilo')
    self.assertEqual(event_object.terminal, u'ttys002')
    self.assertEqual(event_object.status, u'DEAD_PROCESS')
    expected_msg = (
        u'User: moxilo Status: '
        u'DEAD_PROCESS '
        u'Computer Name: localhost '
        u'Terminal: ttys002')
    expected_msg_short = (
        u'User: moxilo')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
