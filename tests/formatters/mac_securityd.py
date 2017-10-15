#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the  Mac OS X ASL securityd log file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_securityd

from tests.formatters import test_lib


class MacSecuritydLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the ASL securityd log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_securityd.MacSecuritydLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_securityd.MacSecuritydLogFormatter()

    expected_attribute_names = [
        'sender',
        'sender_pid',
        'level',
        'facility',
        'message']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
