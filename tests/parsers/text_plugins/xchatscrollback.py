#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the xchatscrollback log parser."""

import unittest

from plaso.parsers.text_plugins import xchatscrollback

from tests.parsers.text_plugins import test_lib


class XChatScrollbackLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the xchatscrollback log parser."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = xchatscrollback.XChatScrollbackLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['xchatscrollback.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-16T02:56:19+00:00',
        'text': '* Speaking now on ##plaso##'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-16T02:56:27+00:00',
        'text': '* Joachim \xe8 uscito (Client exited)'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-18T21:58:36+00:00',
        'text': 'Tcl interface unloaded'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-18T21:58:36+00:00',
        'text': 'Python interface unloaded'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # TODO: change parser to return NotSet semantic time.
    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '1970-01-01T00:00:00+00:00',
        'nickname': 'fpi',
        'text': '0 is a good timestamp',
        'timestamp': 0}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-26T08:50:56+00:00',
        'text': '* Topic of #plasify \xe8: .'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-26T08:51:02+00:00'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-26T08:52:12+00:00',
        'nickname': 'fpi',
        'text': 'Hi Kristinn!'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:scrollback:line',
        'date_time': '2009-01-26T08:53:13+00:00',
        'nickname': 'Kristinn',
        'text': 'GO AND WRITE PARSERS!!! O_o'}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)


if __name__ == '__main__':
  unittest.main()
