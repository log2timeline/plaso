#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the plist event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist

from tests.formatters import test_lib


class PlistFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the plist event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = plist.PlistFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = plist.PlistFormatter()

    expected_attribute_names = [
        'root',
        'key',
        'desc']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
