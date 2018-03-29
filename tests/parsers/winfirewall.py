#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Windows firewall log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winfirewall as _  # pylint: disable=unused-import
from plaso.parsers import winfirewall

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinFirewallParserTest(test_lib.ParserTestCase):
  """Tests for the Windows firewall log parser."""

  @shared_test_lib.skipUnlessHasTestFile(['firewall.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = winfirewall.WinFirewallParser()
    storage_writer = self._ParseFile(['firewall.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 15)

    events = list(storage_writer.GetSortedEvents())

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2005-04-11 08:06:02.000000')

    self.assertEqual(event.source_ip, '123.45.78.90')
    self.assertEqual(event.dest_ip, '123.156.78.90')

    event = events[7]

    self.CheckTimestamp(event.timestamp, '2005-04-11 08:06:26.000000')

    self.assertEqual(event.size, 576)
    self.assertEqual(event.flags, 'A')
    self.assertEqual(event.tcp_ack, 987654321)

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

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[9]

    self.assertEqual(event.icmp_type, 8)
    self.assertEqual(event.icmp_code, 0)


if __name__ == '__main__':
  unittest.main()
