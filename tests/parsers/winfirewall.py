#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows firewall log parser."""

import unittest

from plaso.formatters import winfirewall as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import winfirewall

from tests.parsers import test_lib


class WinFirewallParserTest(test_lib.ParserTestCase):
  """Tests for the Windows firewall log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = winfirewall.WinFirewallParser()
    storage_writer = self._ParseFile(
        [u'firewall.log'], parser_object)

    self.assertEqual(len(storage_writer.events), 15)

    event_object = storage_writer.events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2005-04-11 08:06:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.source_ip, u'123.45.78.90')
    self.assertEqual(event_object.dest_ip, u'123.156.78.90')

    event_object = storage_writer.events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2005-04-11 08:06:26')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.size, 576)
    self.assertEqual(event_object.flags, u'A')
    self.assertEqual(event_object.tcp_ack, 987654321)

    expected_msg = (
        u'DROP [ TCP RECEIVE ] '
        u'From: 123.45.78.90 :80 > 123.156.78.90 :1774 '
        u'Size (bytes): 576 '
        u'Flags [A] '
        u'TCP Seq Number: 123456789 '
        u'TCP ACK Number: 987654321 '
        u'TCP Window Size (bytes): 12345')
    expected_msg_short = (
        u'DROP [TCP] 123.45.78.90 : 80 > 123.156.78.90 : 1774')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = storage_writer.events[9]

    self.assertEqual(event_object.icmp_type, 8)
    self.assertEqual(event_object.icmp_code, 0)


if __name__ == '__main__':
  unittest.main()
