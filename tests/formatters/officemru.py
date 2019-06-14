#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Office MRU Windows Registry event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import officemru

from tests.formatters import test_lib


class OfficeMRUWindowsRegistryEventFormatter(
    test_lib.EventFormatterTestCase):
  """Tests for the Microsoft Office MRU Windows Registry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = officemru.OfficeMRUWindowsRegistryEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = officemru.OfficeMRUWindowsRegistryEventFormatter()

    expected_attribute_names = [
        'key_path',
        'value_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
