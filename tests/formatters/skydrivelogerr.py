#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SkyDrive error log event formatter."""

import unittest

from plaso.formatters import skydrivelogerr

from tests.formatters import test_lib


class SkyDriveLogErrorFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SkyDrive error log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skydrivelogerr.SkyDriveLogErrorFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skydrivelogerr.SkyDriveLogErrorFormatter()

    expected_attribute_names = [
        u'module',
        u'source_code',
        u'text',
        u'detail']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
