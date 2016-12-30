#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache event formatters."""

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

    expected_attribute_names = [u'url', u'content_length']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
