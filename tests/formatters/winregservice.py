#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows services event formatter."""

import unittest

from plaso.formatters import winregservice

from tests.formatters import test_lib


class WinRegistryServiceFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows service event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winregservice.WinRegistryServiceFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winregservice.WinRegistryServiceFormatter()

    expected_attribute_names = [
        u'key_path',
        u'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
