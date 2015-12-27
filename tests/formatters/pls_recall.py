#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PL/SQL Recall event formatter."""

import unittest

from plaso.formatters import pls_recall

from tests.formatters import test_lib


class PlsRecallFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PL/SQL Recall file container event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pls_recall.PlsRecallFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pls_recall.PlsRecallFormatter()

    expected_attribute_names = [
        u'sequence',
        u'username',
        u'database_name',
        u'query']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
