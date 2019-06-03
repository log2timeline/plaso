#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry key or value event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg

from tests.formatters import test_lib


class WinRegistryGenericFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Registry key or value event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winreg.WinRegistryGenericFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winreg.WinRegistryGenericFormatter()

    expected_attribute_names = [
        'key_path',
        'values']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
