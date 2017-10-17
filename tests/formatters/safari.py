#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari history event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import safari

from tests.formatters import test_lib


class SafariHistoryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Safari history event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = safari.SafariHistoryFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = safari.SafariHistoryFormatter()

    expected_attribute_names = [
        'url',
        'title',
        'display_title',
        'visit_count']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
