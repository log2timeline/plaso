#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the CUPS IPP file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import cups_ipp

from tests.formatters import test_lib


class CupsIppFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the CUPS IPP event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = cups_ipp.CupsIppFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = cups_ipp.CupsIppFormatter()

    expected_attribute_names = [
        'status', 'user', 'owner', 'job_name', 'application', 'type_doc',
        'printer_id']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
