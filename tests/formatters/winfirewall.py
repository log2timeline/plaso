#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows firewall log file event formatter."""

import unittest

from plaso.formatters import winfirewall

from tests.formatters import test_lib


class WinFirewallFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows firewall log entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winfirewall.WinFirewallFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winfirewall.WinFirewallFormatter()

    expected_attribute_names = [
        u'action',
        u'protocol',
        u'path',
        u'source_ip',
        u'source_port',
        u'dest_ip',
        u'dest_port',
        u'size',
        u'flags',
        u'tcp_seq',
        u'tcp_ack',
        u'tcp_win',
        u'icmp_type',
        u'icmp_code',
        u'info']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
