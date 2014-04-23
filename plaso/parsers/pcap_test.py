#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors..
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the PCAP parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import pcap as pcap_formatter
from plaso.lib import event
from plaso.parsers import pcap
from plaso.parsers import test_lib


class PCAPParserTest(test_lib.ParserTestCase):
  """Tests for the PCAP parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = pcap.PcapParser(pre_obj)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['test.pcap'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # PCAP information:
    #    Number of streams: 96

    self.assertEquals(len(event_objects), 96)

    # Test stream 3.
    #    Protocol:        TCP
    #    Source IP:       192.168.195.130
    #    Dest IP:         63.245.217.43
    #    Source Port:     1038
    #    Dest Port:       443
    #    Stream Type:     SSL
    #    Starting Packet: 4
    #    Ending Packet:   6

    event_object = event_objects[3]
    self.assertEquals(event_object.packet_count, 3)
    self.assertEquals(event_object.protocol, u'TCP')
    self.assertEquals(event_object.source_ip, u'192.168.195.130')
    self.assertEquals(event_object.dest_ip, u'63.245.217.43')
    self.assertEquals(event_object.dest_port, 443)
    self.assertEquals(event_object.source_port, 1038)
    self.assertEquals(event_object.stream_type, u'SSL')
    self.assertEquals(event_object.first_packet_id, 4)
    self.assertEquals(event_object.last_packet_id, 6)

    # Test stream 6.
    #    Protocol:        UDP
    #    Source IP:       192.168.195.130
    #    Dest IP:         192.168.195.2
    #    Source Port:     55679
    #    Dest Port:       53
    #    Stream Type:     DNS
    #    Starting Packet: 4
    #    Ending Packet:   6
    #    Protocol Data:   DNS Query for  wpad.localdomain

    event_object = event_objects[6]
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

    event_object = event_object.event_objects[0]

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
        u'Last Packet ID: 1307')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()

