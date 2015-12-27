#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X application usage event formatter."""

import unittest

from plaso.formatters import appusage

from tests.formatters import test_lib


class ApplicationUsageFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Mac OS X Application usage event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = appusage.ApplicationUsageFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = appusage.ApplicationUsageFormatter()

    expected_attribute_names = [
        u'application', u'app_version', u'bundle_id', u'count']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
