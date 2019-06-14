#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the file history ESE database event formatter."""

from __future__ import unicode_literals

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
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = (
        file_history.FileHistoryNamespaceEventFormatter())

    expected_attribute_names = [
        'original_filename', 'identifier', 'parent_identifier',
        'file_attribute', 'usn_number']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
