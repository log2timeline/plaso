#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the file system stat event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import file_system

from tests.formatters import test_lib


class FileStatEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the file system stat event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = file_system.FileStatEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = file_system.FileStatEventFormatter()

    expected_attribute_names = [
        'display_name', 'file_entry_type', 'unallocated']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class NTFSFileStatEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the NFTS file system stat event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = file_system.NTFSFileStatEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = file_system.NTFSFileStatEventFormatter()

    expected_attribute_names = [
        'attribute_name', 'display_name', 'file_reference', 'name',
        'parent_file_reference', 'path_hints', 'unallocated']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
