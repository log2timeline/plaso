#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome cookies database event formatter."""

import unittest

from plaso.formatters import chrome_cookies
from plaso.formatters import test_lib


class ChromeCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Chrome cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = chrome_cookies.ChromeCookieFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = chrome_cookies.ChromeCookieFormatter()

    expected_attribute_names = [
        u'url', u'cookie_name', u'httponly', u'persistent']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
