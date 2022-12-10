#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the LS Quarantine database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import ls_quarantine

from tests.parsers.sqlite_plugins import test_lib


class MacOSLSQuarantinePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the LS Quarantine database plugin."""

  def testProcess(self):
    """Tests the Process function on a LS Quarantine database file."""
    plugin = ls_quarantine.MacOSLSQuarantinePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['quarantine.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'agent': 'Google Chrome',
        'data': (
            'http://download.mackeeper.zeobit.com/package.php?'
            'key=460245286&trt=5&landpr=Speedtest'),
        'data_type': 'macos:lsquarantine:entry',
        'downloaded_time': '2013-07-12T19:30:16.000000+00:00',
        'url': (
            'http://mackeeperapp.zeobit.com/aff/speedtest.net.6/download.php?'
            'affid=460245286&trt=5&utm_campaign=3ES&tid_ext=P107fSKcSfqpMbcP3'
            'sI4fhKmeMchEB3dkAGpX4YIsvM;US;L;1')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 10)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
