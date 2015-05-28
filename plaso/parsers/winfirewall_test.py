#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows firewall log parser."""

import unittest

from plaso.formatters import winfirewall as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import test_lib
from plaso.parsers import winfirewall


class WinFirewallParserTest(test_lib.ParserTestCase):
  """Tests for the Windows firewall log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = winfirewall.WinFirewallParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'firewall.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 15)

    event_object = event_objects[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2005-04-11 08:06:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.source_ip, u'123.45.78.90')
    self.assertEqual(event_object.dest_ip, u'123.156.78.90')

    event_object = event_objects[7]

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

    event_object = event_objects[9]

    self.assertEqual(event_object.icmp_type, 8)
    self.assertEqual(event_object.icmp_code, 0)


if __name__ == '__main__':
  unittest.main()
