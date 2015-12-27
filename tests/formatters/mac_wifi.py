#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X wifi.log file event formatter."""

import unittest

from plaso.formatters import mac_wifi

from tests.formatters import test_lib


class MacWifiLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the wifi.log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_wifi.MacWifiLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_wifi.MacWifiLogFormatter()

    expected_attribute_names = [
        u'action',
        u'user',
        u'function',
        u'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
