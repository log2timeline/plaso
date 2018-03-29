#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the PCAP event formatter."""

from __future__ import unicode_literals

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
        'source_ip',
        'dest_ip',
        'source_port',
        'dest_port',
        'protocol',
        'stream_type',
        'size',
        'protocol_data',
        'stream_data',
        'first_packet_id',
        'last_packet_id',
        'packet_count']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
