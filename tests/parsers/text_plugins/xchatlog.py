#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the xchatlog text parser plugin."""

import unittest

from plaso.parsers.text_plugins import xchatlog

from tests.parsers.text_plugins import test_lib


class XChatLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the xchatlog text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = xchatlog.XChatLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['xchat.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2011-12-31 21:11:55',
        'data_type': 'xchat:log:line',
        'text': 'XChat start logging'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:log:line',
        'text': '--> You are now talking on #gugle'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:log:line',
        'text': '--- Topic for #gugle is plaso, a difficult word'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:log:line',
        'text': 'Topic for #gugle set by Kristinn'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:log:line',
        'text': '--- Joachim gives voice to fpi'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:log:line',
        'text': '* XChat here'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'xchat:log:line',
        'nickname': 'fpi',
        'text': 'ola plas-ing guys!'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'date_time': '2011-12-31 23:00:00',
        'data_type': 'xchat:log:line',
        'nickname': 'STRANGER',
        'text': '\u65e5\u672c'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'date_time': '2011-12-31 23:59:00',
        'data_type': 'xchat:log:line',
        'text': 'XChat end logging'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

  def testProcessWithTimeZone(self):
    """Tests the Process function with a time zone."""
    plugin = xchatlog.XChatLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['xchat.log'], plugin, timezone='Europe/Rome')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2011-12-31 21:11:55',
        'data_type': 'xchat:log:line',
        'text': 'XChat start logging',
        'timestamp': '2011-12-31 20:11:55.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
