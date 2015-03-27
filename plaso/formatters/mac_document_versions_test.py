#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X appfirewall.log file event formatter."""

import unittest

from plaso.formatters import mac_document_versions
from plaso.formatters import test_lib


class MacDocumentVersionsFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Mac OS X Document Versions page visited event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_document_versions.MacDocumentVersionsFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_document_versions.MacDocumentVersionsFormatter()

    expected_attribute_names = [
        u'name',
        u'path',
        u'version_path',
        u'user_sid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
