#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android Application Usage event formatter."""

import unittest

from plaso.formatters import android_app_usage
from plaso.formatters import test_lib


class AndroidApplicationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android Application Last Resumed event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = android_app_usage.AndroidApplicationFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = android_app_usage.AndroidApplicationFormatter()

    expected_attribute_names = [u'package', u'component']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
