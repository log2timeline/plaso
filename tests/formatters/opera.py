#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Opera history event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import opera

from tests.formatters import test_lib


class OperaGlobalHistoryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Opera global history event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = opera.OperaGlobalHistoryFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = opera.OperaGlobalHistoryFormatter()

    expected_attribute_names = [
        'url',
        'title',
        'description']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class OperaTypedHistoryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Opera typed history event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = opera.OperaTypedHistoryFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = opera.OperaTypedHistoryFormatter()

    expected_attribute_names = [
        'url',
        'entry_selection']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
