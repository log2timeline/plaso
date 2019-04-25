#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Recycler/Recycle Bin event formatter."""

from __future__ import unicode_literals

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
        'drive_letter',
        'original_filename',
        'record_index',
        'short_filename']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
