#!/usr/bin/env python3
"""Tests for the Windows firewall log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import winfirewall

from tests.parsers.text_plugins import test_lib


class WinFirewallLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Windows firewall log text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = winfirewall.WinFirewallLogTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'#Version: 1.5\n'
        b'#Software: Microsoft Windows Firewall\n'
        b'#Time Format: Local\n'
        b'#Fields: date time action protocol src-ip dst-ip src-port '
        b'dst-port size tcpflags tcpsyn tcpack tcpwin icmptype icmpcode info '
        b'path\n'
        b'2005-04-11 08:05:57 DROP UDP 123.45.78.90 123.156.78.255 '
        b'137 137 78 - - - - - - - RECEIVE\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcess(self):
    """Tests the Process function."""
    plugin = winfirewall.WinFirewallLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['windows_firewall.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 15)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:firewall_log:entry',
        'destination_ip': '123.156.78.90',
        'destination_port': 1774,
        'last_written_time': '2005-04-11T08:06:26',
        'source_ip': '123.45.78.90',
        'source_port': 80,
        'packet_size': 576,
        'tcp_ack': 987654321,
        'tcp_flags': 'A',
        'tcp_sequence_number': 123456789,
        'tcp_window_size': 12345}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
