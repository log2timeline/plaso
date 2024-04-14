#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Container Runtime Interface (CRI) log text plugin."""

import unittest

from plaso.parsers.text_plugins import cri

from tests.parsers.text_plugins import test_lib


class CRILogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the CRI log text parser plugin."""

  def testProcess(self):
    """Tests for the CheckRequiredFormat method."""
    plugin = cri.CRITextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['cri.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'cri:container:log:entry',
        'event_datetime': '2016-10-06T00:17:09.669794202+00:00',
        'message': ' log content 1',
        'stream': 'stdout',
        'tag': 'P'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'cri:container:log:entry',
        'event_datetime': '2016-10-06T00:17:09.669794203+00:00',
        'message': ' log content 2',
        'stream': 'stderr',
        'tag': 'F'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
