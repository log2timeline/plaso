#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome history event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome

from tests.formatters import test_lib


class ChromePageVisitedFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Chrome page visited event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = chrome.ChromePageVisitedFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = chrome.ChromePageVisitedFormatter()

    expected_attribute_names = [
        'url',
        'title',
        'typed_count',
        'from_visit',
        'visit_source',
        'page_transition',
        'extra']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
