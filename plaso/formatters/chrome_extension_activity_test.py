#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome extension activity database event formatter."""

import unittest

from plaso.formatters import chrome_extension_activity
from plaso.formatters import test_lib


class ChromeExtensionActivityEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Chrome extension activity event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (
        chrome_extension_activity.ChromeExtensionActivityEventFormatter())
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (
        chrome_extension_activity.ChromeExtensionActivityEventFormatter())

    expected_attribute_names = [
      u'extension_id', u'action_type', u'activity_id', u'page_url',
      u'page_title', u'api_name', u'args', u'other']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
