#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the file system stat event formatter."""

import unittest

from plaso.formatters import filestat

from tests.formatters import test_lib


class FileStatFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the file system stat event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = filestat.FileStatFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = filestat.FileStatFormatter()

    expected_attribute_names = [u'display_name', u'unallocated']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
