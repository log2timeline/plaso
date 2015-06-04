#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MSIECF event formatters."""

import unittest

from plaso.formatters import msiecf

from tests.formatters import test_lib


class MsiecfLeakFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF leak item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfLeakFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msiecf.MsiecfLeakFormatter()

    expected_attribute_names = [
        u'cached_file_path',
        u'cached_file_size',
        u'recovered_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class MsiecfRedirectedFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF redirected item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfRedirectedFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msiecf.MsiecfRedirectedFormatter()

    expected_attribute_names = [
        u'url',
        u'recovered_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class MsiecfUrlFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF URL item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfUrlFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msiecf.MsiecfUrlFormatter()

    expected_attribute_names = [
        u'url',
        u'number_of_hits',
        u'cached_file_path',
        u'cached_file_size',
        u'http_headers',
        u'recovered_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
