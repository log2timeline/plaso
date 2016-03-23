#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Office MRU Windows Registry event formatter."""

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
        u'key_path',
        u'value_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
