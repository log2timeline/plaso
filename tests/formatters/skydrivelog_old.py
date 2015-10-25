#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SkyDrive old log event formatter."""

import unittest

from plaso.formatters import skydrivelog_old

from tests.formatters import test_lib


class SkyDriveOldLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SkyDrive old log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skydrivelog_old.SkyDriveOldLogFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skydrivelog_old.SkyDriveOldLogFormatter()

    expected_attribute_names = [
        u'source_code',
        u'log_level',
        u'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
