#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome Preferences file event formatter."""

import unittest

from plaso.formatters import chrome_preferences

from tests.formatters import test_lib


class ChromeExtensionInstallationEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Chrome extension installation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (
        chrome_preferences.ChromeExtensionInstallationEventFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (
        chrome_preferences.ChromeExtensionInstallationEventFormatter())

    expected_attribute_names = [
        u'extension_id', u'extension_name', u'path']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


# TODO: add tests for ChromeExtensionsAutoupdaterEvent
# TODO: add tests for ChromeExtensionInstallationEventFormatter
# TODO: add tests for ChromeContentSettingsExceptionsFormatter


if __name__ == '__main__':
  unittest.main()
