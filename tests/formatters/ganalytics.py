#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Analytics cookie event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import ganalytics

from tests.formatters import test_lib


class AnalyticsUtmaCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMA Google Analytics cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ganalytics.AnalyticsUtmaCookieFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ganalytics.AnalyticsUtmaCookieFormatter()

    expected_attribute_names = [
        'url', 'cookie_name', 'sessions', 'domain_hash', 'visitor_id']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class AnalyticsUtmbCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMB Google Analytics cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ganalytics.AnalyticsUtmbCookieFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ganalytics.AnalyticsUtmbCookieFormatter()

    expected_attribute_names = [
        'url', 'cookie_name', 'pages_viewed', 'domain_hash']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class AnalyticsUtmtCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMT Google Analytics cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ganalytics.AnalyticsUtmtCookieFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ganalytics.AnalyticsUtmtCookieFormatter()

    expected_attribute_names = ['url', 'cookie_name']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class AnalyticsUtmzCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMZ Google Analytics cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ganalytics.AnalyticsUtmzCookieFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ganalytics.AnalyticsUtmzCookieFormatter()

    expected_attribute_names = [
        'url', 'cookie_name', 'sessions', 'domain_hash', 'sources',
        'utmcsr', 'utmccn', 'utmcmd', 'utmctr', 'utmcct']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
