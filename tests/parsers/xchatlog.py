#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the xchatlog parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import xchatlog

from tests.parsers import test_lib


class XChatLogUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatlog parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = xchatlog.XChatLogParser()
    storage_writer = self._ParseFile(
        ['xchat.log'], parser, timezone='Europe/Rome')

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'text': 'XChat start logging',
        'timestamp': '2011-12-31 20:11:55.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'text': '--> You are now talking on #gugle'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'text': '--- Topic for #gugle is plaso, a difficult word'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'text': 'Topic for #gugle set by Kristinn'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'text': '--- Joachim gives voice to fpi'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'text': '* XChat here'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'nickname': 'fpi',
        'text': 'ola plas-ing guys!'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'nickname': 'STRANGER',
        'text': '\u65e5\u672c',
        'timestamp': '2011-12-31 22:00:00.000000'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'text': 'XChat end logging',
        'timestamp': '2011-12-31 22:59:00.000000'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_message = '[nickname: STRANGER] \u65e5\u672c'

    event_data = self._GetEventDataOfEvent(storage_writer, events[7])
    self._TestGetMessageStrings(event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
