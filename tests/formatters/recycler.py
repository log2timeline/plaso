#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Recycler/Recycle Bin event formatter."""

import unittest

from plaso.formatters import recycler

from tests.formatters import test_lib


class WinRecyclerFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Recycler/Recycle Bin event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = recycler.WinRecyclerFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = recycler.WinRecyclerFormatter()

    expected_attribute_names = [
        u'drive_letter',
        u'original_filename',
        u'record_index',
        u'short_filename']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
