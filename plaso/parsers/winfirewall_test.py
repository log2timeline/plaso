#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
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
"""Tests for the Windows firewall log parser."""
import os
import unittest

# pylint: disable-msg=W0611
from plaso.formatters import winfirewall as winformatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import winfirewall

import pytz


class WinFirewallParserTest(unittest.TestCase):
  """Tests for the Windows firewall log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.utc
    self._parser = winfirewall.WinFirewallParser(pre_obj, None)

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testParseFile(self):
    """Read a fireall log file and run a few tests."""
    test_file = os.path.join('test_data', 'firewall.log')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self._parser.Parse(file_object))

    self.assertEquals(len(events), 15)

    udp_event = events[4]

    self.assertEquals(udp_event.source_ip, '123.45.78.90')
    self.assertEquals(udp_event.dest_ip, '123.156.78.90')
    # expr `date -u -d "2005-04-11 08:06:02" +"%s%N"` \/ 1000
    self.assertEquals(udp_event.timestamp, 1113206762000000)

    tcp_event = events[7]
    icmp_event = events[9]

    self.assertEquals(tcp_event.size, 576)
    self.assertEquals(tcp_event.flags, 'A')
    self.assertEquals(tcp_event.tcp_ack, 987654321)
    # expr `date -u -d "2005-04-11 08:06:26" +"%s%N"` \/ 1000
    self.assertEquals(tcp_event.timestamp, 1113206786000000)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
        tcp_event)
    expected_string = (
        u'DROP [ TCP RECEIVE ] From: 123.45.78.90 :80 > 123.156.78.90 :1774 '
        'Size (bytes): 576 Flags [A] TCP Seq Number: 123456789 TCP ACK Number: '
        '987654321 TCP Window Size (bytes): 12345')
    self.assertEquals(msg, expected_string)

    self.assertEquals(icmp_event.icmp_type, 8)
    self.assertEquals(icmp_event.icmp_code, 0)


if __name__ == '__main__':
  unittest.main()
