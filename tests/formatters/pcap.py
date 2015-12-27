#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PCAP event formatter."""

import unittest

from plaso.formatters import pcap

from tests.formatters import test_lib


class PCAPFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PCAP event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pcap.PCAPFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pcap.PCAPFormatter()

    expected_attribute_names = [
        u'source_ip',
        u'dest_ip',
        u'source_port',
        u'dest_port',
        u'protocol',
        u'stream_type',
        u'size',
        u'protocol_data',
        u'stream_data',
        u'first_packet_id',
        u'last_packet_id',
        u'packet_count']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
