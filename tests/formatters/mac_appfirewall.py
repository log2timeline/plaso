#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS appfirewall.log file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_appfirewall

from tests.formatters import test_lib


class MacAppFirewallLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MacOS appfirewall.log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_appfirewall.MacAppFirewallLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_appfirewall.MacAppFirewallLogFormatter()

    expected_attribute_names = [
        'computer_name',
        'agent',
        'status',
        'process_name',
        'action']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
