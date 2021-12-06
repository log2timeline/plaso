#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the xchatscrollback log parser."""

import unittest

from plaso.parsers import xchatscrollback

from tests.parsers import test_lib


class XChatScrollbackUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatscrollback log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = xchatscrollback.XChatScrollbackParser()
    storage_writer = self._ParseFile(['xchatscrollback.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2009-01-16 02:56:19',
        'data_type': 'xchat:scrollback:line',
        'text': '* Speaking now on ##plaso##'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2009-01-16 02:56:27',
        'data_type': 'xchat:scrollback:line',
        'text': '* Joachim \xe8 uscito (Client exited)'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2009-01-18 21:58:36',
        'data_type': 'xchat:scrollback:line',
        'text': 'Tcl interface unloaded'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'date_time': '2009-01-18 21:58:36',
        'data_type': 'xchat:scrollback:line',
        'text': 'Python interface unloaded'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # TODO: change parser to return NotSet semantic time.
    expected_event_values = {
        'date_time': '1970-01-01 00:00:00',
        'data_type': 'xchat:scrollback:line',
        'nickname': 'fpi',
        'text': '0 is a good timestamp',
        'timestamp': 0}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'date_time': '2009-01-26 08:50:56',
        'data_type': 'xchat:scrollback:line',
        'text': '* Topic of #plasify \xe8: .'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'date_time': '2009-01-26 08:51:02',
        'data_type': 'xchat:scrollback:line'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'date_time': '2009-01-26 08:52:12',
        'data_type': 'xchat:scrollback:line',
        'nickname': 'fpi',
        'text': 'Hi Kristinn!'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'date_time': '2009-01-26 08:53:13',
        'data_type': 'xchat:scrollback:line',
        'nickname': 'Kristinn',
        'text': 'GO AND WRITE PARSERS!!! O_o'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)


if __name__ == '__main__':
  unittest.main()
