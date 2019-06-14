#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows services event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import services

from tests.formatters import test_lib


class WinRegistryServiceFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows service event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = services.WinRegistryServiceFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = services.WinRegistryServiceFormatter()

    expected_attribute_names = [
        'error_control',
        'image_path',
        'key_path',
        'service_type',
        'start_type',
        'values']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
