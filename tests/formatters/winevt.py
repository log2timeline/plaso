#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows EventLog (EVT) file event formatter."""

import unittest

from plaso.formatters import winevt

from tests.formatters import test_lib


class WinEVTFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows EventLog (EVT) record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winevt.WinEVTFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winevt.WinEVTFormatter()

    expected_attribute_names = [
        u'event_identifier',
        u'severity',
        u'record_number',
        u'event_type',
        u'event_category',
        u'source_name',
        u'computer_name',
        u'message_string',
        u'strings']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
