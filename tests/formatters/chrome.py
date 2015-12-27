#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome history event formatters."""

import unittest

from plaso.formatters import chrome

from tests.formatters import test_lib


class ChromeFileDownloadFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Chrome file download event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = chrome.ChromeFileDownloadFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = chrome.ChromeFileDownloadFormatter()

    expected_attribute_names = [
        u'url', u'full_path', u'received_bytes', u'total_bytes']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


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
        u'url', u'title', u'typed_count', u'host', u'from_visit',
        u'visit_source', u'extra']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
