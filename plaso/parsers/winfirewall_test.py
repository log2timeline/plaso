#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

import unittest

# pylint: disable=unused-import
from plaso.formatters import winfirewall as winfirewall_formatter
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import winfirewall


class WinFirewallParserTest(test_lib.ParserTestCase):
  """Tests for the Windows firewall log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = winfirewall.WinFirewallParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['firewall.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 15)

    event_object = event_objects[4]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2005-04-11 08:06:02')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.source_ip, '123.45.78.90')
    self.assertEquals(event_object.dest_ip, '123.156.78.90')

    event_object = event_objects[7]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2005-04-11 08:06:26')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(event_object.size, 576)
    self.assertEquals(event_object.flags, 'A')
    self.assertEquals(event_object.tcp_ack, 987654321)

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

    self.assertEquals(event_object.icmp_type, 8)
    self.assertEquals(event_object.icmp_code, 0)


if __name__ == '__main__':
  unittest.main()
