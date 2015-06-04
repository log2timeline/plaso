#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari Binary cookie event formatter."""

import unittest

from plaso.formatters import safari_cookies

from tests.formatters import test_lib


class SafaryCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Safari Binary Cookie file entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = safari_cookies.SafaryCookieFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = safari_cookies.SafaryCookieFormatter()

    expected_attribute_names = [
        u'url',
        u'path',
        u'cookie_name',
        u'flags']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
