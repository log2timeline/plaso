#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shutdown Windows Registry event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import shutdown

from tests.formatters import test_lib


class ShutdownWindowsRegistryEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the shutdown Windows Registry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = shutdown.ShutdownWindowsRegistryEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = shutdown.ShutdownWindowsRegistryEventFormatter()

    expected_attribute_names = [
        'key_path',
        'value_name']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
