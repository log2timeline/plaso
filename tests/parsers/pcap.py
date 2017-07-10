#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PCAP parser."""

import unittest

from plaso.formatters import pcap  # pylint: disable=unused-import
from plaso.parsers import pcap

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class PcapParserTest(test_lib.ParserTestCase):
  """Tests for the PCAP parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'test.pcap'])
  def testParse(self):
    """Tests the Parse function."""
    parser = pcap.PcapParser()
    storage_writer = self._ParseFile([u'test.pcap'], parser)

    # PCAP information:
    #    Number of streams: 96 (TCP: 47, UDP: 39, ICMP: 0, Other: 10)
    #
    # For each stream 2 events are generated one for the start
    # and one for the end time.

    self.assertEqual(storage_writer.number_of_events, 192)

    events = list(storage_writer.GetEvents())

    # Test stream 3 (event 6).
    #    Protocol:        TCP
    #    Source IP:       192.168.195.130
    #    Dest IP:         63.245.217.43
    #    Source Port:     1038
    #    Dest Port:       443
    #    Stream Type:     SSL
    #    Starting Packet: 4
    #    Ending Packet:   6

    event = events[6]
    self.assertEqual(event.packet_count, 3)
    self.assertEqual(event.protocol, u'TCP')
    self.assertEqual(event.source_ip, u'192.168.195.130')
    self.assertEqual(event.dest_ip, u'63.245.217.43')
    self.assertEqual(event.dest_port, 443)
    self.assertEqual(event.source_port, 1038)
    self.assertEqual(event.stream_type, u'SSL')
    self.assertEqual(event.first_packet_id, 4)
    self.assertEqual(event.last_packet_id, 6)

    # Test stream 6 (event 12).
    #    Protocol:        UDP
    #    Source IP:       192.168.195.130
    #    Dest IP:         192.168.195.2
    #    Source Port:     55679
    #    Dest Port:       53
    #    Stream Type:     DNS
    #    Starting Packet: 4
    #    Ending Packet:   6
    #    Protocol Data:   DNS Query for  wpad.localdomain

    event = events[12]
    self.assertEqual(event.packet_count, 5)
    self.assertEqual(event.protocol, u'UDP')
    self.assertEqual(event.source_ip, u'192.168.195.130')
    self.assertEqual(event.dest_ip, u'192.168.195.2')
    self.assertEqual(event.dest_port, 53)
    self.assertEqual(event.source_port, 55679)
    self.assertEqual(event.stream_type, u'DNS')
    self.assertEqual(event.first_packet_id, 11)
    self.assertEqual(event.last_packet_id, 1307)
    self.assertEqual(
        event.protocol_data, u'DNS Query for  wpad.localdomain')

    expected_message = (
        u'Source IP: 192.168.195.130 '
        u'Destination IP: 192.168.195.2 '
        u'Source Port: 55679 '
        u'Destination Port: 53 '
        u'Protocol: UDP '
        u'Type: DNS '
        u'Size: 380 '
        u'Protocol Data: DNS Query for  wpad.localdomain '
        u'Stream Data: \'\\xb8\\x9c\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00'
        u'\\x00\\x00\\x04wpad\\x0blocaldomain\\x00\\x00\\x01\\x00\\x01\\xb8'
        u'\\x9c\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x04wpa\' '
        u'First Packet ID: 11 '
        u'Last Packet ID: 1307 '
        u'Packet Count: 5')
    expected_short_message = (
        u'Type: DNS '
        u'First Packet ID: 11')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
