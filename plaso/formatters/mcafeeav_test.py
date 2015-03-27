#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the McAfee AV Logs file event formatter."""

import unittest

from plaso.formatters import mcafeeav
from plaso.formatters import test_lib


class McafeeAccessProtectionLogEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the McAfee Access Protection Log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mcafeeav.McafeeAccessProtectionLogEventFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mcafeeav.McafeeAccessProtectionLogEventFormatter()

    expected_attribute_names = [
        u'filename',
        u'username',
        u'trigger_location',
        u'status',
        u'rule',
        u'action']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
