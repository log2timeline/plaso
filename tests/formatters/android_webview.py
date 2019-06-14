#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android WebView database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_webview

from tests.formatters import test_lib


class AndroidWebViewCookieEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Android WebView formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = android_webview.AndroidWebViewCookieEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = android_webview.AndroidWebViewCookieEventFormatter()

    expected_attribute_names = [
        'domain', 'path', 'name', 'value', 'secure']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
