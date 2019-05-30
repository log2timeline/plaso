#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android Application Usage event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_app_usage

from tests.formatters import test_lib


class AndroidApplicationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android Application Last Resumed event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = android_app_usage.AndroidApplicationFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = android_app_usage.AndroidApplicationFormatter()

    expected_attribute_names = ['package', 'component']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
