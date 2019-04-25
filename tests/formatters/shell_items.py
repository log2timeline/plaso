#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shell item event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import shell_items

from tests.formatters import test_lib


class ShellItemFileEntryEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the shell item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = shell_items.ShellItemFileEntryEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = shell_items.ShellItemFileEntryEventFormatter()

    expected_attribute_names = [
        'name',
        'long_name',
        'localized_name',
        'file_reference',
        'shell_item_path',
        'origin']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
