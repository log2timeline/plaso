#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the xchatscrollback log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import xchatscrollback as _  # pylint: disable=unused-import
from plaso.parsers import xchatscrollback

from tests.parsers import test_lib


class XChatScrollbackUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatscrollback log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = xchatscrollback.XChatScrollbackParser()
    storage_writer = self._ParseFile(['xchatscrollback.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2009-01-16 02:56:19.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[] * Speaking now on ##plaso##'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2009-01-16 02:56:27.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[] * Joachim \xe8 uscito (Client exited)'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2009-01-18 21:58:36.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[] Tcl interface unloaded'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2009-01-18 21:58:36.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[] Python interface unloaded'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[5]
    self.assertEqual(event.timestamp, 0)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[nickname: fpi] 0 is a good timestamp'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[6]

    self.CheckTimestamp(event.timestamp, '2009-01-26 08:50:56.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[] * Topic of #plasify \xe8: .'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[7]

    self.CheckTimestamp(event.timestamp, '2009-01-26 08:51:02.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    event = events[8]

    self.CheckTimestamp(event.timestamp, '2009-01-26 08:52:12.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[nickname: fpi] Hi Kristinn!'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[9]

    self.CheckTimestamp(event.timestamp, '2009-01-26 08:53:13.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = '[nickname: Kristinn] GO AND WRITE PARSERS!!! O_o'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
