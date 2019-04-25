#!/usr/bin/env python3
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

    expected_attribute_names = ['url', 'title', 'display_title', 'visit_count']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SafariHistoryFormatterSqlite(test_lib.EventFormatterTestCase):
  """Tests for the Safari history event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = safari.SafariHistoryFormatterSqlite()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = safari.SafariHistoryFormatterSqlite()

    expected_attribute_names = [
        'url', 'title', 'visit_count', 'was_http_non_get']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
