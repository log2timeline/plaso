#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the xchatscrollback log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import xchatscrollback as xchatscrollback_formatter
from plaso.parsers import xchatscrollback

from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatScrollbackUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatscrollback log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = xchatscrollback.XChatScrollbackParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'xchatscrollback.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 10)

    # TODO: refactor this to use timelib.
    self.assertEqual(event_objects[0].timestamp, 1232074579000000)
    self.assertEqual(event_objects[1].timestamp, 1232074587000000)
    self.assertEqual(event_objects[2].timestamp, 1232315916000000)
    self.assertEqual(event_objects[3].timestamp, 1232315916000000)
    self.assertEqual(event_objects[4].timestamp, 1232959856000000)
    self.assertEqual(event_objects[5].timestamp, 0)
    self.assertEqual(event_objects[7].timestamp, 1232959862000000)
    self.assertEqual(event_objects[8].timestamp, 1232959932000000)
    self.assertEqual(event_objects[9].timestamp, 1232959993000000)

    expected_string = u'[] * Speaking now on ##plaso##'
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string)

    expected_string = u'[] * Joachim \xe8 uscito (Client exited)'
    self._TestGetMessageStrings(
        event_objects[1], expected_string, expected_string)

    expected_string = u'[] Tcl interface unloaded'
    self._TestGetMessageStrings(
        event_objects[2], expected_string, expected_string)

    expected_string = u'[] Python interface unloaded'
    self._TestGetMessageStrings(
        event_objects[3], expected_string, expected_string)

    expected_string = u'[] * Topic of #plasify \xe8: .'
    self._TestGetMessageStrings(
        event_objects[6], expected_string, expected_string)

    expected_string = u'[nickname: fpi] Hi Kristinn!'
    self._TestGetMessageStrings(
        event_objects[8], expected_string, expected_string)

    expected_string = u'[nickname: Kristinn] GO AND WRITE PARSERS!!! O_o'
    self._TestGetMessageStrings(
        event_objects[9], expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
