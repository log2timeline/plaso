#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SkyDrive log event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import skydrivelog

from tests.formatters import test_lib


class SkyDriveLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SkyDrive log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skydrivelog.SkyDriveLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skydrivelog.SkyDriveLogFormatter()

    expected_attribute_names = [
        'module',
        'source_code',
        'log_level',
        'detail']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SkyDriveOldLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SkyDrive old log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skydrivelog.SkyDriveOldLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skydrivelog.SkyDriveOldLogFormatter()

    expected_attribute_names = [
        'source_code',
        'log_level',
        'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
