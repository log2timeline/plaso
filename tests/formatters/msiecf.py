#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MSIECF event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import msiecf

from tests.formatters import test_lib


class MsiecfLeakFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF leak item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfLeakFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msiecf.MsiecfLeakFormatter()

    expected_attribute_names = [
        'cached_file_path',
        'cached_file_size',
        'recovered_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class MsiecfRedirectedFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF redirected item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfRedirectedFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msiecf.MsiecfRedirectedFormatter()

    expected_attribute_names = [
        'url',
        'recovered_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class MsiecfUrlFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MSIECF URL item event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msiecf.MsiecfUrlFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msiecf.MsiecfUrlFormatter()

    expected_attribute_names = [
        'url',
        'number_of_hits',
        'cached_file_path',
        'cached_file_size',
        'http_headers',
        'recovered_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
