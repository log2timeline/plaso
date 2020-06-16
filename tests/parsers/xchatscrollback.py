#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the xchatscrollback log parser."""

from __future__ import unicode_literals

import unittest

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

    expected_event_values = {
        'text': '* Speaking now on ##plaso##',
        'timestamp': '2009-01-16 02:56:19.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'text': '* Joachim \xe8 uscito (Client exited)',
        'timestamp': '2009-01-16 02:56:27.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'text': 'Tcl interface unloaded',
        'timestamp': '2009-01-18 21:58:36.000000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'text': 'Python interface unloaded',
        'timestamp': '2009-01-18 21:58:36.000000'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'nickname': 'fpi',
        'text': '0 is a good timestamp',
        'timestamp': 0}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'text': '* Topic of #plasify \xe8: .',
        'timestamp': '2009-01-26 08:50:56.000000'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'timestamp': '2009-01-26 08:51:02.000000'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'nickname': 'fpi',
        'text': 'Hi Kristinn!',
        'timestamp': '2009-01-26 08:52:12.000000'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'nickname': 'Kristinn',
        'text': 'GO AND WRITE PARSERS!!! O_o',
        'timestamp': '2009-01-26 08:53:13.000000'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

    expected_message = '[nickname: Kristinn] GO AND WRITE PARSERS!!! O_o'

    event_data = self._GetEventDataOfEvent(storage_writer, events[9])
    self._TestGetMessageStrings(event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
