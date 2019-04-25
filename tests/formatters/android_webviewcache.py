#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_webviewcache

from tests.formatters import test_lib


class AndroidWebViewCacheFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android WebViewCache formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = android_webviewcache.AndroidWebViewCacheFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = android_webviewcache.AndroidWebViewCacheFormatter()

    expected_attribute_names = ['url', 'content_length']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
