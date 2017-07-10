#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows firewall log parser."""

import unittest

from plaso.formatters import winfirewall  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import winfirewall

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinFirewallParserTest(test_lib.ParserTestCase):
  """Tests for the Windows firewall log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'firewall.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = winfirewall.WinFirewallParser()
    storage_writer = self._ParseFile([u'firewall.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 15)

    events = list(storage_writer.GetEvents())

    event = events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2005-04-11 08:06:02')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.source_ip, u'123.45.78.90')
    self.assertEqual(event.dest_ip, u'123.156.78.90')

    event = events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2005-04-11 08:06:26')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.size, 576)
    self.assertEqual(event.flags, u'A')
    self.assertEqual(event.tcp_ack, 987654321)

    expected_message = (
        u'DROP [ TCP RECEIVE ] '
        u'From: 123.45.78.90 :80 > 123.156.78.90 :1774 '
        u'Size (bytes): 576 '
        u'Flags [A] '
        u'TCP Seq Number: 123456789 '
        u'TCP ACK Number: 987654321 '
        u'TCP Window Size (bytes): 12345')
    expected_short_message = (
        u'DROP [TCP] 123.45.78.90 : 80 > 123.156.78.90 : 1774')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[9]

    self.assertEqual(event.icmp_type, 8)
    self.assertEqual(event.icmp_code, 0)


if __name__ == '__main__':
  unittest.main()
