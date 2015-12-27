#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Opera history event formatters."""

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
        u'url',
        u'title',
        u'description']

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
        u'url',
        u'entry_selection']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
