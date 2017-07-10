#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the xchatlog parser."""

import unittest

from plaso.formatters import xchatlog  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import xchatlog

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatLogUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatlog parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'xchat.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = xchatlog.XChatLogParser()
    storage_writer = self._ParseFile(
        [u'xchat.log'], parser, timezone=u'Europe/Rome')

    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-12-31 21:11:55+01:00')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'XChat start logging'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[1]
    expected_message = u'--> You are now talking on #gugle'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[2]
    expected_message = u'--- Topic for #gugle is plaso, a difficult word'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[3]
    expected_message = u'Topic for #gugle set by Kristinn'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[4]
    expected_message = u'--- Joachim gives voice to fpi'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[5]
    expected_message = u'* XChat here'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[6]
    expected_message = u'[nickname: fpi] ola plas-ing guys!'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[7]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-12-31 23:00:00+01:00')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'[nickname: STRANGER] \u65e5\u672c'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[8]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-12-31 23:59:00+01:00')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'XChat end logging'
    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
