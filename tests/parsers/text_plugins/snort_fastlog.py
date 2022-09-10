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
        ['snort3_alert_fast.log'], plugin,
        knowledge_base_values={'year': 2021})

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test the following single line entry in snort3-format that has
    # no classification-field:
    #
    # 12/28-12:55:38.765402 [**] [1:366:11] "PROTOCOL-ICMP PING Unix"
    # [**] [Priority: 3] {ICMP} 2001:df1:c200:c:0:0:0:35 ->
    # 2001:4860:4860::8888

    expected_event_values = {
        'classification': None,
        'data_type': 'snort:fastlog:alert',
        'date_time': '2021-12-28 12:55:38.765402',
        'destination_ip': '2001:4860:4860:0:0:0:0:8888',
        'message': 'PROTOCOL-ICMP PING Unix',
        'priority': 3,
        'protocol': 'ICMP',
        'rule_identifier': '1:366:11',
        'source_ip': '2001:df1:c200:c:0:0:0:35'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test the following single line entry in snort3-format that has
    # no priority-field:
    #
    # 09/01-12:55:37.785027 [**] [1:408:8] "PROTOCOL-ICMP Echo Reply"
    # [**] [Classification: Misc activity] [Priority: 3]
    # {ICMP} 8.8.8.8 -> 192.168.178.179

    expected_event_values = {
        'classification': 'Misc activity',
        'data_type': 'snort:fastlog:alert',
        'date_time': '2021-12-28 12:55:38.885027',
        'destination_ip': '2001:df1:c200:c:0:0:0:35',
        'message': 'PROTOCOL-ICMP Echo Reply',
        #'priority': None,
        'protocol': 'ICMP',
        'rule_identifier': '1:408:8',
        'source_ip': '2001:4860:4860:0:0:0:0:8888'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Test the following single line entry in snort3-format. This
    # should check correct incrementation of the year:
    #
    # 01/02-11:30:23.358639 [**] [1:648:18] "INDICATOR-SHELLCODE x86 NOOP"
    # [**] [Classification: Executable code was detected] [Priority: 1]
    # {TCP} 10.6.6.254:80 -> 10.6.6.103:60884

    expected_event_values = {
        'classification': 'Executable code was detected',
        'data_type': 'snort:fastlog:alert',
        'date_time': '2022-01-02 11:30:23.358639',
        'destination_ip': '10.6.6.103',
        'destination_port': 60884,
        'message': 'INDICATOR-SHELLCODE x86 NOOP',
        'priority': 1,
        'protocol': 'TCP',
        'rule_identifier': '1:648:18',
        'source_ip': '10.6.6.254',
        'source_port': 80}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Test the following single line entry in snort3-format that
    # houses IPv6 addresses and ports:
    #
    # 02/04-23:41:31.115933 [**] [1:20035:1000] "MALWARE-CNC outbound
    # connection" [**] [Classification: Attempted # Information Leak]
    # [Priority: 1] {TCP} 10.6.6.103:60884 -> 10.6.6.254:80

    expected_event_values = {
        'classification': 'Attempted Information Leak',
        'data_type': 'snort:fastlog:alert',
        'date_time': '2022-02-04 23:41:31.115933',
        'destination_ip': '2001:4860:4860:0:0:0:0:8888',
        'destination_port': 80,
        'message': 'MALWARE-CNC outbound connection',
        'priority': 1,
        'protocol': 'TCP',
        'rule_identifier': '1:20035:1000',
        'source_ip': '2001:df1:c200:c:0:0:0:35',
        'source_port': 60884}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

  def testProcessWithSuricataLog(self):
    """Tests the Process function with a Suricata fast-log alert log file."""
    plugin = snort_fastlog.SnortFastLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['suricata_alert_fast.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test the following single line entry in suricata-format:
    #
    # 10/05/10-10:08:59.667372 [**] [1:2009187:4] ET WEB_CLIENT ACTIVEX
    # iDefense COMRaider ActiveX Control Arbitrary File Deletion
    # [**] [Classification: Web Application Attack] [Priority: 3]
    # {TCP} 11.11.232.144:80 -> 192.168.1.4:56068

    expected_event_values = {
        'classification': 'Web Application Attack',
        'data_type': 'snort:fastlog:alert',
        'date_time': '2010-05-10 10:08:59.667372',
        'destination_ip': '192.168.1.4',
        'destination_port': 56068,
        'message': (
            'ET WEB_CLIENT ACTIVEX iDefense COMRaider ActiveX Control '
            'Arbitrary File Deletion'),
        'priority': 3,
        'protocol': 'TCP',
        'rule_identifier': '1:2009187:4',
        'source_ip': '11.11.232.144',
        'source_port': 80}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test the following single line entry in suricata-format that has
    # no classification-field:
    #
    # 21/12/28-12:55:38.765402 [**] [1:366:11] PROTOCOL-ICMP PING Unix
    # [**] [Priority: 3] {ICMP} 2001:df1:c200:c:0:0:0:35 ->
    # 2001:4860:4860::8888

    expected_event_values = {
        'classification': None,
        'data_type': 'snort:fastlog:alert',
        'date_time': '2021-12-28 12:55:38.765402',
        'destination_ip': '2001:4860:4860:0:0:0:0:8888',
        'message': 'PROTOCOL-ICMP PING Unix',
        'priority': 3,
        'protocol': 'ICMP',
        'rule_identifier': '1:366:11',
        'source_ip': '2001:df1:c200:c:0:0:0:35'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Test the following single line entry in snort3-format that has
    # no priority-field:
    #
    # 22/09/01-12:55:37.785027 [**] [1:408:8] PROTOCOL-ICMP Echo Reply
    # [**] [Classification: Misc activity] [Priority: 3]
    # {ICMP} 8.8.8.8 -> 192.168.178.179

    expected_event_values = {
        'classification': 'Misc activity',
        'data_type': 'snort:fastlog:alert',
        'date_time': '2021-12-28 12:55:38.885027',
        'destination_ip': '2001:df1:c200:c:0:0:0:35',
        'message': 'PROTOCOL-ICMP Echo Reply',
        'priority': None,
        'protocol': 'ICMP',
        'rule_identifier': '1:408:8',
        'source_ip': '2001:4860:4860:0:0:0:0:8888'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Test the following single line entry in suricata-format. This
    # should check correct incrementation of the year:
    #
    # 23/01/02-11:30:23.358639 [**] [1:648:18] INDICATOR-SHELLCODE x86 NOOP
    # [**] [Classification: Executable code was detected] [Priority: 1]
    # {TCP} 10.6.6.254:80 -> 10.6.6.103:60884

    expected_event_values = {
        'classification': 'Executable code was detected',
        'data_type': 'snort:fastlog:alert',
        'date_time': '2022-01-02 11:30:23.358639',
        'destination_ip': '10.6.6.103',
        'destination_port': 60884,
        'message': 'INDICATOR-SHELLCODE x86 NOOP',
        'priority': 1,
        'protocol': 'TCP',
        'rule_identifier': '1:648:18',
        'source_ip': '10.6.6.254',
        'source_port': 80}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Test the following single line entry in suricata-format that
    # houses IPv6 addresses and ports:
    #
    # 23/02/04-23:41:31.115933 [**] [1:20035:1000] MALWARE-CNC
    # outbound connection [**] [Classification: Attempted
    # Information Leak] [Priority: 1] {TCP} 10.6.6.103:60884 ->
    # 10.6.6.254:80

    expected_event_values = {
        'classification': 'Attempted Information Leak',
        'data_type': 'snort:fastlog:alert',
        'date_time': '2022-02-04 23:41:31.115933',
        'destination_ip': '2001:4860:4860:0:0:0:0:8888',
        'destination_port': 80,
        'message': 'MALWARE-CNC outbound connection',
        'priority': 1,
        'protocol': 'TCP',
        'rule_identifier': '1:20035:1000',
        'source_ip': '2001:df1:c200:c:0:0:0:35',
        'source_port': 60884}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
