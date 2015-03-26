#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Firefox cookie entry event formatter."""

import unittest

from plaso.formatters import firefox_cookies
from plaso.formatters import test_lib


class FirefoxCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox cookie entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox_cookies.FirefoxCookieFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox_cookies.FirefoxCookieFormatter()

    expected_attribute_names = [
        u'url', u'cookie_name', u'httponly', u'ga_data']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
