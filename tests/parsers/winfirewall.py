#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows firewall log parser."""

import unittest

from plaso.parsers import winfirewall

from tests.parsers import test_lib


class WinFirewallParserTest(test_lib.ParserTestCase):
  """Tests for the Windows firewall log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winfirewall.WinFirewallParser()
    storage_writer = self._ParseFile(['firewall.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 15)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2005-04-11 08:06:02',
        'data_type': 'windows:firewall:log_entry',
        'dest_ip': '123.156.78.90',
        'source_ip': '123.45.78.90'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'date_time': '2005-04-11 08:06:26',
        'data_type': 'windows:firewall:log_entry',
        'dest_ip': '123.156.78.90',
        'dest_port': 1774,
        'flags': 'A',
        'source_ip': '123.45.78.90',
        'source_port': 80,
        'size': 576,
        'tcp_ack': 987654321,
        'tcp_seq': 123456789,
        'tcp_win': 12345}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'data_type': 'windows:firewall:log_entry',
        'icmp_code': 0,
        'icmp_type': 8}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = winfirewall.WinFirewallParser()
    storage_writer = self._ParseFile(['firewall.log'], parser, timezone='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 15)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2005-04-11 08:06:02',
        'data_type': 'windows:firewall:log_entry',
        'dest_ip': '123.156.78.90',
        'source_ip': '123.45.78.90',
        'timestamp': '2005-04-11 06:06:02.000000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
