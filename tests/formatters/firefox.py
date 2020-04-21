#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox history event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import firefox

from tests.formatters import test_lib


class FirefoxPageVisitFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox page visited event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxPageVisitFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxPageVisitFormatter()

    expected_attribute_names = [
        'url', 'title', 'visit_count', 'host', 'extra_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
