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
    self.assertEqual(number_of_event_data, 17)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'cri:container:log:entry',
        'event_datetime': '2016-10-06T00:17:09.669794202+00:00',
        'body': ' log content 1',
        'stream': 'stdout',
        'tag': 'P'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'cri:container:log:entry',
        'event_datetime': '2016-10-06T00:17:09.669794203+00:00',
        'body': ' log content 2',
        'stream': 'stderr',
        'tag': 'F'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'cri:container:log:entry',
        'event_datetime': '2024-04-16T06:25:29.095207860+00:00',
        'body': (
            ' 10.0.2.1:39914 - - [Tue, 16 Apr 2024 06:25:29 UTC] '
            '"GET /readiness HTTP/1.1" kube-probe/1.27'),
        'stream': 'stdout',
        'tag': 'F'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 14)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
