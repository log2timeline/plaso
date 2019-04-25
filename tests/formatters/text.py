#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the text file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import text

from tests.formatters import test_lib


class TextEntryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the text file entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = text.TextEntryFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = text.TextEntryFormatter()

    expected_attribute_names = ['text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
