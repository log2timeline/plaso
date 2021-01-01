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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 15)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'dest_ip': '123.156.78.90',
        'source_ip': '123.45.78.90',
        'timestamp': '2005-04-11 08:06:02.000000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'flags': 'A',
        'size': 576,
        'tcp_ack': 987654321,
        'timestamp': '2005-04-11 08:06:26.000000'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_message = (
        'DROP [ TCP RECEIVE ] '
        'From: 123.45.78.90 :80 > 123.156.78.90 :1774 '
        'Size (bytes): 576 '
        'Flags [A] '
        'TCP Seq Number: 123456789 '
        'TCP ACK Number: 987654321 '
        'TCP Window Size (bytes): 12345')
    expected_short_message = (
        'DROP [TCP] 123.45.78.90 : 80 > 123.156.78.90 : 1774')

    event_data = self._GetEventDataOfEvent(storage_writer, events[7])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'icmp_code': 0,
        'icmp_type': 8}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = winfirewall.WinFirewallParser()
    storage_writer = self._ParseFile(['firewall.log'], parser, timezone='CET')

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 15)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'timestamp': '2005-04-11 06:06:02.000000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
