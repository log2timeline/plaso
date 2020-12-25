#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome Preferences file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_preferences

from tests.formatters import test_lib


class ChromeContentSettingsExceptionsFormatter(
    test_lib.EventFormatterTestCase):
  """Tests for the Chrome extension installation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (
        chrome_preferences.ChromeContentSettingsExceptionsFormatter())
    self.assertIsNotNone(event_formatter)

  # TODO: add test for FormatEventValues.


if __name__ == '__main__':
  unittest.main()
