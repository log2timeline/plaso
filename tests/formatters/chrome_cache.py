#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome Cache files event formatter."""

import unittest

from plaso.formatters import chrome_cache

from tests.formatters import test_lib


class ChromeCacheEntryEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Chrome Cache entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = chrome_cache.ChromeCacheEntryEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = chrome_cache.ChromeCacheEntryEventFormatter()

    expected_attribute_names = [u'original_url']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
