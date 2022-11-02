#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SkyDrive version 1 log files text parser plugin."""

import unittest

from plaso.parsers.text_plugins import skydrivelog1

from tests.parsers.text_plugins import test_lib


class SkyDriveLog1TextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the SkyDrive version 1 log files text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = skydrivelog1.SkyDriveLog1TextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['skydrive_v1.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 18)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 18)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2013-08-01T21:22:28.999+00:00',
        'data_type': 'skydrive:log:old:line',
        'log_level': 'DETAIL',
        'source_code': 'global.cpp:626!logVersionInfo',
        'text': '17.0.2011.0627 (Ship)'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
