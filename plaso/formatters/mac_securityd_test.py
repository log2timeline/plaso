#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the  Mac OS X ASL securityd log file event formatter."""

import unittest

from plaso.formatters import mac_securityd
from plaso.formatters import test_lib


class MacSecuritydLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the ASL securityd log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_securityd.MacSecuritydLogFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_securityd.MacSecuritydLogFormatter()

    expected_attribute_names = [
      u'sender',
      u'sender_pid',
      u'level',
      u'facility',
      u'message']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
