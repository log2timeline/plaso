#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the xchatlog parser."""

import unittest

from plaso.formatters import xchatlog as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import xchatlog

from tests.parsers import test_lib

import pytz  # pylint: disable=wrong-import-order


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatLogUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatlog parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = xchatlog.XChatLogParser()
    storage_writer = self._ParseFile(
        [u'xchat.log'], parser_object,
        default_timezone=pytz.timezone(u'Europe/Rome'))

    self.assertEqual(len(storage_writer.events), 9)

    event_object = storage_writer.events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-12-31 21:11:55+01:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'XChat start logging'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[1]
    expected_string = u'--> You are now talking on #gugle'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[2]
    expected_string = u'--- Topic for #gugle is plaso, a difficult word'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[3]
    expected_string = u'Topic for #gugle set by Kristinn'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[4]
    expected_string = u'--- Joachim gives voice to fpi'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[5]
    expected_string = u'* XChat here'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[6]
    expected_string = u'[nickname: fpi] ola plas-ing guys!'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[7]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-12-31 23:00:00+01:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'[nickname: STRANGER] \u65e5\u672c'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[8]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-12-31 23:59:00+01:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'XChat end logging'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
