#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the file system stat event formatter."""

import unittest

from plaso.formatters import filestat


class FileStatFormatterTest(unittest.TestCase):
  """Tests for the file system stat event formatter."""

  def testInitialization(self):
    """Test the initialization."""
    event_formatter = filestat.FileStatFormatter()
    self.assertNotEquals(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = filestat.FileStatFormatter()

    expected_attribute_names = sorted([
        u'display_name', u'unallocated'])

    attribute_names = event_formatter.GetFormatStringAttributeNames()
    self.assertEqual(sorted(attribute_names), expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
