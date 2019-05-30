#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome cookies database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_cookies

from tests.formatters import test_lib


class ChromeCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Chrome cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = chrome_cookies.ChromeCookieFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = chrome_cookies.ChromeCookieFormatter()

    expected_attribute_names = [
        'url', 'cookie_name', 'httponly', 'persistent']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
