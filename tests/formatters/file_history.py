#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the file history ESE database event formatter."""

import unittest

from plaso.formatters import file_history

from tests.formatters import test_lib


class FileHistoryNamespaceEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the file history ESE database event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = (
        file_history.FileHistoryNamespaceEventFormatter())
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (
        file_history.FileHistoryNamespaceEventFormatter())

    expected_attribute_names = [
        u'original_filename', u'identifier', u'parent_identifier',
        u'file_attribute', u'usn_number']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
