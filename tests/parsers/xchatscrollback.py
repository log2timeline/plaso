#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the xchatscrollback log parser."""

import unittest

from plaso.formatters import xchatscrollback  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import xchatscrollback

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatScrollbackUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatscrollback log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'xchatscrollback.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = xchatscrollback.XChatScrollbackParser()
    storage_writer = self._ParseFile([u'xchatscrollback.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-16 02:56:19')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[] * Speaking now on ##plaso##'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-16 02:56:27')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[] * Joachim \xe8 uscito (Client exited)'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-18 21:58:36')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[] Tcl interface unloaded'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-18 21:58:36')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[] Python interface unloaded'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[5]
    self.assertEqual(event.timestamp, 0)

    expected_message = u'[nickname: fpi] 0 is a good timestamp'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-26 08:50:56')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[] * Topic of #plasify \xe8: .'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-26 08:51:02')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[8]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-26 08:52:12')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[nickname: fpi] Hi Kristinn!'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-01-26 08:53:13')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[nickname: Kristinn] GO AND WRITE PARSERS!!! O_o'
    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
