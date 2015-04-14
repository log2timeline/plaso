#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows NT Registry (REGF) file event formatter."""

import unittest

from plaso.formatters import test_lib
from plaso.formatters import winreg


class WinRegistryGenericFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Registry key or value event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winreg.WinRegistryGenericFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winreg.WinRegistryGenericFormatter()

    expected_attribute_names = [
        u'keyname',
        u'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
