#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome Preferences file event formatter."""

import unittest

from plaso.formatters import chrome_preferences

from tests.formatters import test_lib


class ChromePreferencesPrimaryURLFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Google Chrome preferences primary URL formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = (
        chrome_preferences.ChromePreferencesPrimaryURLFormatterHelper())

    output_mediator = self._CreateOutputMediator()

    event_values = {'primary_url': 'https://example.com'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['primary_url'], 'https://example.com')

    event_values = {'primary_url': ''}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['primary_url'], 'local file')

    event_values = {'primary_url': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['primary_url'])


class ChromePreferencesSecondaryURLFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Google Chrome preferences secondary URL formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = (
        chrome_preferences.ChromePreferencesSecondaryURLFormatterHelper())

    output_mediator = self._CreateOutputMediator()

    event_values = {
        'primary_url': 'https://example.com',
        'secondary_url': 'https://anotherexample.com'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(
        event_values['secondary_url'], 'https://anotherexample.com')

    event_values = {
        'primary_url': 'https://example.com',
        'secondary_url': 'https://example.com'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['secondary_url'])

    event_values = {
        'primary_url': 'https://example.com',
        'secondary_url': ''}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['secondary_url'], 'local file')

    event_values = {
        'primary_url': 'https://example.com',
        'secondary_url': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['secondary_url'])


if __name__ == '__main__':
  unittest.main()
