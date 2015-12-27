#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the file system stat event formatter."""

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

    expected_attribute_names = [u'display_name', u'unallocated']

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
        u'attribute_name', u'display_name', u'file_reference', u'name',
        u'parent_file_reference', u'unallocated']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
