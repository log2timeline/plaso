#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Analytics cookie event formatters."""

import unittest

from plaso.formatters import ganalytics

from tests.formatters import test_lib


class AnalyticsUtmaCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMA Google Analytics cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ganalytics.AnalyticsUtmaCookieFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ganalytics.AnalyticsUtmaCookieFormatter()

    expected_attribute_names = [
        u'url', u'cookie_name', u'sessions', u'domain_hash', u'visitor_id']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class AnalyticsUtmbCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMB Google Analytics cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ganalytics.AnalyticsUtmbCookieFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ganalytics.AnalyticsUtmbCookieFormatter()

    expected_attribute_names = [
        u'url', u'cookie_name', u'pages_viewed', u'domain_hash']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class AnalyticsUtmzCookieFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMZ Google Analytics cookie event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ganalytics.AnalyticsUtmzCookieFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ganalytics.AnalyticsUtmzCookieFormatter()

    expected_attribute_names = [
        u'url', u'cookie_name', u'sessions', u'domain_hash', u'sources',
        u'utmcsr', u'utmccn', u'utmcmd', u'utmctr', u'utmcct']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
