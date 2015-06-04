#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X appfirewall.log file event formatter."""

import unittest

from plaso.formatters import mac_appfirewall

from tests.formatters import test_lib


class MacAppFirewallLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Mac OS X appfirewall.log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_appfirewall.MacAppFirewallLogFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_appfirewall.MacAppFirewallLogFormatter()

    expected_attribute_names = [
        u'computer_name',
        u'agent',
        u'status',
        u'process_name',
        u'action']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
