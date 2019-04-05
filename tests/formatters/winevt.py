#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows EventLog (EVT) file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winevt

from tests.formatters import test_lib


class WinEVTFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows EventLog (EVT) record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winevt.WinEVTFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winevt.WinEVTFormatter()

    expected_attribute_names = [
        'event_identifier',
        'severity',
        'record_number',
        'event_type',
        'event_category',
        'source_name',
        'computer_name',
        'message_string',
        'strings']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
