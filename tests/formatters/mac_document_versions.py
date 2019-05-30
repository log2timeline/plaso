#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS appfirewall.log file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_document_versions

from tests.formatters import test_lib


class MacDocumentVersionsFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the MacOS Document Versions page visited event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_document_versions.MacDocumentVersionsFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_document_versions.MacDocumentVersionsFormatter()

    expected_attribute_names = [
        'name',
        'path',
        'version_path',
        'user_sid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
