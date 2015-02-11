#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PCAP parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import pcap as pcap_formatter
from plaso.parsers import pcap
from plaso.parsers import test_lib


class PcapParserTest(test_lib.ParserTestCase):
  """Tests for the PCAP parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = pcap.PcapParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['test.pcap'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # PCAP information:
    #    Number of streams: 96 (TCP: 47, UDP: 39, ICMP: 0, Other: 10)
    #
    # For each stream 2 event objects are generated one for the start
    # and one for the end time.

    self.assertEquals(len(event_objects), 192)

    # Test stream 3 (event object 6).
    #    Protocol:        TCP
    #    Source IP:       192.168.195.130
    #    Dest IP:         63.245.217.43
    #    Source Port:     1038
    #    Dest Port:       443
    #    Stream Type:     SSL
    #    Starting Packet: 4
    #    Ending Packet:   6

    event_object = event_objects[6]
    self.assertEquals(event_object.packet_count, 3)
    self.assertEquals(event_object.protocol, u'TCP')
    self.assertEquals(event_object.source_ip, u'192.168.195.130')
    self.assertEquals(event_object.dest_ip, u'63.245.217.43')
    self.assertEquals(event_object.dest_port, 443)
    self.assertEquals(event_object.source_port, 1038)
    self.assertEquals(event_object.stream_type, u'SSL')
    self.assertEquals(event_object.first_packet_id, 4)
    self.assertEquals(event_object.last_packet_id, 6)

    # Test stream 6 (event object 12).
    #    Protocol:        UDP
    #    Source IP:       192.168.195.130
    #    Dest IP:         192.168.195.2
    #    Source Port:     55679
    #    Dest Port:       53
    #    Stream Type:     DNS
    #    Starting Packet: 4
    #    Ending Packet:   6
    #    Protocol Data:   DNS Query for  wpad.localdomain

    event_object = event_objects[12]
    self.assertEquals(event_object.packet_count, 5)
    self.assertEquals(event_object.protocol, u'UDP')
    self.assertEquals(event_object.source_ip, u'192.168.195.130')
    self.assertEquals(event_object.dest_ip, u'192.168.195.2')
    self.assertEquals(event_object.dest_port, 53)
    self.assertEquals(event_object.source_port, 55679)
    self.assertEquals(event_object.stream_type, u'DNS')
    self.assertEquals(event_object.first_packet_id, 11)
    self.assertEquals(event_object.last_packet_id, 1307)
    self.assertEquals(
        event_object.protocol_data, u'DNS Query for  wpad.localdomain')

    expected_msg = (
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
    expected_msg_short = (
        u'Type: DNS '
        u'First Packet ID: 11')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
