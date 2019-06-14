#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox cache record event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import firefox_cache

from tests.formatters import test_lib


class FirefoxCacheFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox cache record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox_cache.FirefoxCacheFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox_cache.FirefoxCacheFormatter()

    expected_attribute_names = [
        'fetch_count', 'response_code', 'request_method', 'url']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
