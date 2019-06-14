#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Restore Point (rp.log) file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winrestore

from tests.formatters import test_lib


class RestorePointInfoFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Restore Point information event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winrestore.RestorePointInfoFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winrestore.RestorePointInfoFormatter()

    expected_attribute_names = [
        'description',
        'restore_point_event_type',
        'restore_point_type']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
