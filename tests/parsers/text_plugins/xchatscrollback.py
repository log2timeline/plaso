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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2009-01-16T02:56:19+00:00',
        'data_type': 'xchat:scrollback:line',
        'text': '* Speaking now on ##plaso##'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
