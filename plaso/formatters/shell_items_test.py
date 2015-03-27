#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the shell item event formatter."""

import unittest

from plaso.formatters import shell_items
from plaso.formatters import test_lib


class ShellItemFileEntryEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the shell item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = shell_items.ShellItemFileEntryEventFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = shell_items.ShellItemFileEntryEventFormatter()

    expected_attribute_names = [
        u'name',
        u'long_name',
        u'localized_name',
        u'file_reference',
        u'shell_item_path',
        u'origin']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
