#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows XML EventLog (EVTX) file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winevtx

from tests.formatters import test_lib


class WinEVTXFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows XML EventLog (EVTX) record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winevtx.WinEVTXFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winevtx.WinEVTXFormatter()

    expected_attribute_names = [
        'event_identifier',
        'record_number',
        'event_level',
        'source_name',
        'computer_name',
        'message_string',
        'strings']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
