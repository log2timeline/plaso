#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Snort3/Suricata fast-log alert log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import snort_fastlog

from tests.parsers.text_plugins import test_lib


class SnortFastLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Snort3/Suricata fast-log alert log text parser plugin."""

  def testProcessWithSnort3Log(self):
    """Tests the Process function with a Snort fast-log alert log file."""
    plugin = snort_fastlog.SnortFastLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['snort3_alert_fast.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'classification': None,
        'data_type': 'snort:fastlog:alert',
        'destination_ip': '2001:4860:4860:0:0:0:0:8888',
        'message': 'PROTOCOL-ICMP PING Unix',
        'last_written_time': '0000-12-28T12:55:38.765402',
        'priority': 3,
        'protocol': 'ICMP',
        'rule_identifier': '1:366:11',
        'source_ip': '2001:df1:c200:c:0:0:0:35'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessWithSuricataLog(self):
    """Tests the Process function with a Suricata fast-log alert log file."""
    plugin = snort_fastlog.SnortFastLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['suricata_alert_fast.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'classification': 'Web Application Attack',
        'data_type': 'snort:fastlog:alert',
        'destination_ip': '192.168.1.4',
        'destination_port': 56068,
        'last_written_time': '2010-05-10T10:08:59.667372',
        'message': (
            'ET WEB_CLIENT ACTIVEX iDefense COMRaider ActiveX Control '
            'Arbitrary File Deletion'),
        'priority': 3,
        'protocol': 'TCP',
        'rule_identifier': '1:2009187:4',
        'source_ip': '11.11.232.144',
        'source_port': 80}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
