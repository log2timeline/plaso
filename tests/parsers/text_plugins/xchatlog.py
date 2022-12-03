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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2011-12-31T21:11:55',
        'data_type': 'xchat:log:line',
        'nickname': None,
        'text': 'XChat start logging'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
