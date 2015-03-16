#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Drive snapshots event formatter."""

import unittest

from plaso.formatters import gdrive
from plaso.formatters import test_lib


class GDriveCloudEntryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Drive snapshot cloud event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = gdrive.GDriveCloudEntryFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = gdrive.GDriveCloudEntryFormatter()

    expected_attribute_names = [
        u'path', u'shared', u'size', u'url', u'document_type']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class GDriveLocalEntryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Drive snapshot local event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = gdrive.GDriveLocalEntryFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = gdrive.GDriveLocalEntryFormatter()

    expected_attribute_names = [u'path', u'size']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
