#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows firewall log file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winfirewall

from tests.formatters import test_lib


class WinFirewallFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows firewall log entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winfirewall.WinFirewallFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winfirewall.WinFirewallFormatter()

    expected_attribute_names = [
        'action',
        'protocol',
        'path',
        'source_ip',
        'source_port',
        'dest_ip',
        'dest_port',
        'size',
        'flags',
        'tcp_seq',
        'tcp_ack',
        'tcp_win',
        'icmp_type',
        'icmp_code',
        'info']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
