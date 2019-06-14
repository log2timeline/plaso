#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the McAfee AV Logs file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mcafeeav

from tests.formatters import test_lib


class McafeeAccessProtectionLogEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the McAfee Access Protection Log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mcafeeav.McafeeAccessProtectionLogEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mcafeeav.McafeeAccessProtectionLogEventFormatter()

    expected_attribute_names = [
        'filename',
        'username',
        'trigger_location',
        'status',
        'rule',
        'action']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
