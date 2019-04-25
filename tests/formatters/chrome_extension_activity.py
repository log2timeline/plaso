#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome extension activity database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_extension_activity

from tests.formatters import test_lib


class ChromeExtensionActivityEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Chrome extension activity event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (
        chrome_extension_activity.ChromeExtensionActivityEventFormatter())
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (
        chrome_extension_activity.ChromeExtensionActivityEventFormatter())

    expected_attribute_names = [
        'extension_id',
        'action_type',
        'activity_id',
        'page_url',
        'page_title',
        'api_name',
        'args',
        'other']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
