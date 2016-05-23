#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android WebViewCache event formatters."""

import unittest

from plaso.formatters import android_webviewcache

from tests.formatters import test_lib


class WebViewCacheExpirationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android WebViewCache URL Expiration formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (
        android_webviewcache.WebViewCacheURLExpirationEventFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (
        android_webviewcache.WebViewCacheURLExpirationEventFormatter())

    expected_attribute_names = [u'url', u'content_length']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class WebViewCacheModificationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android WebViewCache URL Modification formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (
        android_webviewcache.WebViewCacheURLModificationEventFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (
        android_webviewcache.WebViewCacheURLModificationEventFormatter())

    expected_attribute_names = [u'url', u'content_length']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
